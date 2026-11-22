#!/usr/bin/env python3
"""Independently recompute stored answers for the 25 tasks in modules 1–6.

Run from the repository root. No source files are modified. The mathematical
oracles deliberately use exact integers/Decimal and simple exhaustive geometry,
not code copied from learner solutions or from the existing grading functions.
"""
from collections import Counter
from decimal import Decimal, localcontext
from itertools import combinations_with_replacement, permutations
from pathlib import Path
import json
import math


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def armstrong_numbers(limit):
    # Enumerating digit multisets is independent of an integer-by-integer scan.
    values = set()
    for width in range(1, len(str(limit)) + 1):
        powers = [digit ** width for digit in range(10)]
        for digits in combinations_with_replacement(range(10), width):
            value = sum(powers[digit] for digit in digits)
            if 0 < value < limit and tuple(sorted(map(int, str(value)))) == digits:
                values.add(value)
    return sorted(values)


def matrix(tokens, count):
    return [[next(tokens) for _ in range(count)] for _ in range(count)]


def reference(step_id, data):
    fields = data.split()
    d = lambda value: Decimal(value)
    if step_id == 4643238:
        return "0"
    if step_id == 3262682:
        return str((2 * d(fields[0]) / d("9.8")).sqrt())
    if step_id == 3262692:
        acceleration, time, velocity = map(d, fields)
        return str(velocity * time + acceleration * time * time / 2)
    if step_id == 3262772:
        return str(d(fields[0]) * d("1.001"))
    if step_id == 3262735:
        first, hundredth = map(d, fields)
        delta = (hundredth - first) / 99
        total = sum(first + i * delta for i in range(70))
        return f"{delta}\n{total}"
    if step_id == 3264578:
        a, b = map(int, fields)
        return "ERROR" if a == b == 0 else "YES" if (b and a % b == 0) or (a and b % a == 0) else "NO"
    if step_id == 3269060:
        sides = sorted(map(d, fields))
        return "YES" if sides[0] + sides[1] > sides[2] else "NO"
    if step_id == 3280697:
        x, y = map(int, fields[:2])
        values = list(map(d, fields[2:5]))
        k = d(fields[5])
        original_x, original_y = x, y
        if original_x <= original_y:
            x = 0
        if original_y <= original_x:
            y = 0
        values[values.index(max(values))] -= k
        return " ".join(map(str, [x, y] + values))
    if step_id == 3264622:
        k, x, y = map(d, fields)
        low, high = min(d(0), k), max(d(0), k)
        # Closest point on each of the four closed segments.
        clamp = lambda v: min(high, max(low, v))
        nearest = [(low, clamp(y)), (high, clamp(y)), (clamp(x), low), (clamp(x), high)]
        return str(min(((x - a) ** 2 + (y - b) ** 2).sqrt() for a, b in nearest))
    if step_id == 3280727:
        a, b, c, d0 = map(d, fields)
        sign = 1 if c >= d0 and a < d0 else -1 if c < d0 and a >= d0 else 0
        return "0" if not sign else "ERROR" if not c else str(a + sign * b / c)
    if step_id == 3281279:
        a, b, c, width, height = map(d, fields)
        if min(a, b, c, width, height) <= 0:
            return "Incorrect input"
        return "YES" if any(x <= width and y <= height for x, y, _ in permutations([a, b, c])) else "NO"
    if step_id == 3281287:
        number = int(fields[0])
        ending = "грибов" if 11 <= number % 100 <= 14 else "гриб" if number % 10 == 1 else "гриба" if 2 <= number % 10 <= 4 else "грибов"
        return f"Мы нашли {number} {ending} в лесу"
    if step_id == 3281353:
        width, height, x1, y1, x2, y2, new_width, new_height = map(int, fields)
        distances = []
        if new_width + x2 - x1 <= width and new_height <= height:
            distances += [max(0, new_width - x1), max(0, new_width - (width - x2))]
        if new_height + y2 - y1 <= height and new_width <= width:
            distances += [max(0, new_height - y1), max(0, new_height - (height - y2))]
        return str(min(distances) if distances else -1)
    if step_id == 3177566:
        return "\n".join(f"{i} * {i} = {i*i}" for i in range(int(fields[0])-1, 0, -1))
    if step_id == 3177655:
        k = int(fields[0])
        return "\n".join(" ".join(str(i*j) for j in range(1, k)) for i in range(1, k))
    if step_id == 3299645:
        return "\n".join(map(str, armstrong_numbers(int(fields[0]))))
    if step_id == 3384444:
        number = int(fields[0])
        layer = math.isqrt(number - 1)
        offset = number - layer * layer - 1
        row, column = (offset, layer) if offset <= layer else (layer, 2 * layer - offset)
        return f"{row} {column}"
    if step_id == 3383209:
        n = int(fields[0])
        return str(1 + n * (n - 1) // 2)
    if step_id == 3341723:
        rows, columns = map(int, fields[:2])
        values = list(map(int, fields[2:]))
        minima = 0
        for row in range(rows):
            for column in range(columns):
                value = values[row * columns + column]
                adjacent = [values[r * columns + c] for r in range(max(0, row-1), min(rows, row+2)) for c in range(max(0, column-1), min(columns, column+2)) if (r, c) != (row, column)]
                minima += all(value < neighbor for neighbor in adjacent)
        return str(minima)
    if step_id == 3381234:
        rows, columns = map(int, fields[:2])
        values = list(map(int, fields[2:]))
        return "\n".join(" ".join(str(max(values[r * columns + c] for r in range(row+1) for c in range(column+1))) for column in range(columns)) for row in range(rows))
    if step_id == 3381291:
        digits, index = fields
        from_right = digits[::-1]
        digit = from_right[int(index)]
        return f"{len(set(digits))}\n{digit}\n" + " ".join(str(i) for i, ch in enumerate(from_right) if ch == digit)
    if step_id == 3382745:
        values = list(map(int, fields))
        first, last = sorted([values.index(min(values)), values.index(max(values))])
        values[first+1:last] = [0] * max(0, last-first-1)
        if 2 * values.count(0) > len(values):
            values = [value for value in values if value != 0]
        return " ".join(map(str, values))
    if step_id == 3383135:
        it = iter(map(int, fields))
        n = next(it)
        a = matrix(it, n)
        m = next(it)
        b = matrix(it, m)
        assert n == m
        return "\n".join(" ".join(str(sum(a[i][k] * b[k][j] for k in range(n))) for j in range(n)) for i in range(n))
    if step_id == 4672519:
        m, n = map(int, fields[:2])
        a = list(map(d, fields[2:2+m]))
        b = list(map(d, fields[2+m:]))
        assert len(a) == m and len(b) == n
        return "1" if a[0] - a[-1] >= b[0] - b[-1] else "2"
    if step_id == 4700496:
        it = iter(map(int, fields))
        replies = []
        for _ in range(next(it)):
            n = next(it)
            a = math.prod(next(it) for _ in range(n))
            b = math.prod(next(it) for _ in range(n))
            assert a == b or (max(a, b)-min(a, b)) * 10_000_000 > min(a, b), "relative-gap promise violated"
            replies.append("<" if a < b else ">" if a > b else "=")
        return "\n".join(replies)
    raise ValueError(f"No oracle for step {step_id}")


def main():
    selected = {4643238,3262682,3262692,3262772,3262735,3264578,3269060,3280697,3264622,3280727,3281279,3281287,3281353,3177566,3177655,3299645,3384444,3383209,3341723,3381234,3381291,3382745,3383135,4672519,4700496}
    results = []
    for path in sorted((ROOT / "courses/86957/steps").rglob("*.step")):
        data = json.loads(path.read_text())
        step_id = int(data["id"])
        if step_id not in selected:
            continue
        staged = ROOT / "corrections/86957/steps" / path.parent.name / path.name
        if staged.exists():
            data = json.loads(staged.read_text())
        source = data["block"]["source"]
        namespace = {}
        exec(compile(source["code"], str(path), "exec"), namespace)
        cases = source["test_cases"]
        failures = []
        with localcontext() as context:
            context.prec = 1000
            for index, (dataset, clue) in enumerate(cases):
                answer = reference(step_id, dataset)
                if not namespace["check"](answer, clue):
                    failures.append({"case_index": index, "reference": answer[:200], "stored": clue[:200]})
        results.append({"step_id": step_id, "case_count": len(cases), "failures": failures,
                        "checked_path": str((staged if staged.exists() else path).relative_to(ROOT))})
    assert len(results) == len(selected)
    report = {"method": "Independent exact integer / 1000-digit Decimal mathematical references checked against every stored testcase", "task_count": len(results), "testcase_count": sum(r["case_count"] for r in results), "results": results}
    (OUT / "task_reference_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"task_count": report["task_count"], "testcase_count": report["testcase_count"], "failures": [r for r in results if r["failures"]]}, ensure_ascii=False))
    assert not any(result["failures"] for result in results), "Stored testcase differs from independent reference"


if __name__ == "__main__":
    main()
