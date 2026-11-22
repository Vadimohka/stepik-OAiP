#!/usr/bin/env python3
"""Reproduce selected audit observations without executing code from the export.

Run from any directory: python audit/checks/verify_export_checks.py
Uses Python's standard library. Results describe the pinned export, not live Stepik.
"""
from __future__ import annotations

import json
import math
from decimal import Decimal, localcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = json.loads((ROOT / "courses/86957/course.json").read_text())
STEPS = {s["id"]: s for s in BUNDLE["step_sources"]}
RESULTS = []


def cases(step_id):
    return STEPS[step_id]["block"]["source"]["test_cases"]


def record(step_id, check, **evidence):
    RESULTS.append({"step_id": step_id, "check": check, **evidence})


def exact_trim_checker(step_id, reply, clue):
    code = STEPS[step_id]["block"]["source"]["code"]
    assert "return reply.strip() == clue.strip()" in code
    return reply.strip() == clue.strip()


def verify_observations():
    dataset, clue = cases(3262682)[0]
    assert dataset.strip() == "92"
    with localcontext() as ctx:
        ctx.prec = 50
        time = (2 * Decimal(dataset) / Decimal("9.8")).sqrt()
        reply = f"{time:.9f}"
    assert reply == "4.333071682" and clue == "4.33307168"
    assert not exact_trim_checker(3262682, reply, clue)
    record(3262682, "nine_decimal_places_rejected", test=1, correct_fixed_9=reply,
           stored_answer=clue, accepted_by_exported_comparison=False)

    dataset, clue = cases(3280697)[4]
    x, y, a, b, c, k = map(Decimal, dataset.split())
    assert (x, y, a, b, c, k) == (3000000000, -3, 3000000000, 2, 3, 4)
    reply = "3000000000 0\n2999999996 2 3"
    assert a - k == 2999999996
    assert Decimal(clue.split()[2]) == 3000000000
    assert not exact_trim_checker(3280697, reply, clue)
    record(3280697, "rounded_reference_changes_value", test=5,
           accurate_answer=reply, stored_answer=clue)

    dataset, clue = cases(3280727)[1]
    a, b, c, d = map(Decimal, dataset.split())
    assert (a, b, c, d) == (0, 0, 0, 0)
    # Formula transcribed from the image in this step and visually verified.
    if c >= d and a < d:
        result = a + b / c
    elif c < d and a >= d:
        result = a - b / c
    else:
        result = Decimal(0)
    assert result == 0 and clue == "ERROR"
    record(3280727, "unused_division_branch", test=2, formula_result="0",
           stored_answer=clue)

    dataset, clue = cases(3281353)[0]
    w, h, x1, y1, x2, y2, sw, sh = map(int, dataset.split())
    assert x1 > x2 and y1 > y2
    record(3281353, "invalid_corner_order", test=1,
           lower_left=[x1, y1], upper_right=[x2, y2], stored_answer=clue)

    dataset, clue = cases(3381234)[0]
    reply = "\n".join(line.rstrip() for line in clue.splitlines())
    assert reply.split() == clue.split()
    assert not exact_trim_checker(3381234, reply, clue)
    record(3381234, "matrix_rejected_without_trailing_spaces", test=1,
           same_numeric_tokens=True, accepted_by_exported_comparison=False)

    invalid = []
    for i, (dataset, _) in enumerate(cases(3384518), 1):
        values = list(map(int, dataset.split()))
        assert values[0] == len(values) - 1
        if any(n > 10**9 for n in values[1:]):
            invalid.append({"test": i, "max_n": max(values[1:])})
    assert invalid
    record(3384518, "inputs_exceed_n_limit", promised_max=10**9, invalid_tests=invalid)

    invalid_moduli, non_linewise = [], []
    for i, (dataset, _) in enumerate(cases(3446002), 1):
        tokens = iter(dataset.split())
        count = int(next(tokens))
        for j in range(1, count + 1):
            length, modulus = int(next(tokens)), int(next(tokens))
            first, second = next(tokens), next(tokens)
            if modulus > 10**4:
                invalid_moduli.append({"test": i, "case": j, "m": modulus})
        if len(dataset.splitlines()) != 1 + 3 * count:
            non_linewise.append(i)
    assert invalid_moduli and non_linewise == [3, 4, 5, 7]
    record(3446002, "modulus_exceeds_limit", promised_max=10**4,
           invalid_cases=invalid_moduli)
    record(3446002, "two_strings_not_on_separate_lines", invalid_tests=non_linewise)

    invalid = [{"test": i, "input": data} for i, (data, _) in enumerate(cases(3446094), 1)
               if not all("a" <= ch <= "z" for ch in data.strip())]
    assert invalid == [{"test": 7, "input": "V"}]
    record(3446094, "uppercase_input_despite_lowercase_constraint", invalid_tests=invalid)

    dataset, clue = cases(4738986)[0]
    assert "if reply == clue:" in STEPS[4738986]["block"]["source"]["code"]
    assert "reply.strip()" not in STEPS[4738986]["block"]["source"]["code"]
    assert clue == "1312131"
    record(4738986, "literal_checker_rejects_final_newline", test=1,
           accepted_without_newline=(clue == clue),
           accepted_with_newline=(clue + "\n" == clue),
           scope="Local comparison only; live Stepik preprocessing was not exercised.")

    dataset, clue = cases(5850209)[0]
    assert "IiTP: forever" in dataset and "IiTP = forever" in clue
    record(5850209, "uppercase_key_despite_lowercase_constraint", test=1, key="IiTP")


def verify_reference_answers():
    """Independent reference calculations for selected numeric/string tasks."""
    def check_all(step_id, solver):
        mismatches = []
        for i, (dataset, clue) in enumerate(cases(step_id), 1):
            actual = solver(dataset)
            if actual.split() != clue.split():
                mismatches.append({"test": i, "actual_prefix": actual[:120],
                                   "stored_prefix": clue[:120]})
        record(step_id, "independent_reference", cases=len(cases(step_id)),
               mismatches=mismatches, comparison="whitespace-separated tokens")

    def local_minima(data):
        nums = list(map(int, data.split()))
        rows, cols = nums[:2]
        mat = [nums[2 + i * cols:2 + (i + 1) * cols] for i in range(rows)]
        return str(sum(all(mat[i][j] < mat[r][c]
                           for r in range(max(0, i - 1), min(rows, i + 2))
                           for c in range(max(0, j - 1), min(cols, j + 2))
                           if (r, c) != (i, j)) for i in range(rows) for j in range(cols)))

    def product_compare(data):
        it = iter(map(int, data.split()))
        ans = []
        for _ in range(next(it)):
            n = next(it)
            a = math.prod(next(it) for _ in range(n))
            b = math.prod(next(it) for _ in range(n))
            ans.append("<" if a < b else ">" if a > b else "=")
        return "\n".join(ans)

    def modular_power(data):
        it = iter(map(int, data.split()))
        out = []
        for k, n, t in zip(it, it, it):
            if (k, n, t) == (0, 0, 0):
                break
            out.append(f"Case #{len(out) + 1}: {pow(k, n, 10**t)}")
        return "\n".join(out)

    def largest_odd_sum(data):
        values = list(map(int, data.split()))[1:]
        answers = []
        for n in values:
            total = 0
            while n:
                total += ((n + 1) // 2) ** 2
                n //= 2
            answers.append(str(total))
        return "\n".join(answers)

    def divisible_arrays(data):
        it = iter(map(int, data.split()))
        answers = []
        for _ in range(next(it)):
            n = next(it)
            lo = [next(it) for _ in range(n)]
            hi = [next(it) for _ in range(n)]
            answer = 1
            for i, (a, b) in enumerate(zip(lo, hi), 1):
                answer = answer * max(0, b // i - (a - 1) // i) % 1000000007
            answers.append(str(answer))
        return "\n".join(answers)

    def delete_digit(data):
        values = data.split()
        assert int(values[0]) == len(values) - 1
        answers = []
        for value in values[1:]:
            pos = next((i for i in range(len(value) - 1) if value[i] < value[i + 1]), len(value) - 1)
            answers.append((value[:pos] + value[pos + 1:]).lstrip("0") or "0")
        return "\n".join(answers)

    def anagrams(data):
        word = data.strip()
        return str(math.factorial(len(word)) // math.prod(math.factorial(word.count(c)) for c in set(word)))

    def non_palindrome(data):
        s = data.strip()
        return str(-1 if len(set(s)) == 1 else len(s) - (s == s[::-1]))

    def interesting(data):
        return "\n".join(str((int(x) + 1) // 10) for x in data.split()[1:])

    def bijective_ternary(data):
        n, result = int(data), ""
        while n:
            n, remainder = divmod(n - 1, 3)
            result = str(remainder + 1) + result
        return result

    def yaml_to_ini(data):
        it = iter(data.splitlines())
        files = []
        for _ in range(int(next(it))):
            out, path, previous = [], [], None
            for _ in range(int(next(it))):
                line = next(it)
                depth = (len(line) - len(line.lstrip(" "))) // 4
                key, value = line.strip().split(":", 1)
                path = path[:depth]
                if not value:
                    path.append(key)
                    continue
                current = tuple(path)
                if current != previous:
                    if out:
                        out.append("")
                    if current:
                        out.append("[" + ".".join(current) + "]")
                out.append(key + " = " + value.strip())
                previous = current
            files.append("\n".join(out))
        return "\n\n".join(files) + "\n"

    for step_id, solver in [
        (3341723, local_minima), (4700496, product_compare), (3428255, modular_power),
        (3384518, largest_odd_sum), (5828883, divisible_arrays), (5822035, delete_digit),
        (3446015, anagrams), (3446094, non_palindrome), (3496704, interesting),
        (3496878, bijective_ternary), (5850209, yaml_to_ini),
    ]:
        check_all(step_id, solver)


if __name__ == "__main__":
    verify_observations()
    verify_reference_answers()
    print(json.dumps({"schema_version": 1, "results": RESULTS}, ensure_ascii=False, indent=2))
