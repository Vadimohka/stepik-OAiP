#!/usr/bin/env python3
"""Run focused regression checks for the revised import files, locally.

This executes selected, reviewed Python grading functions and independent C++
reference solutions. It never runs student submissions. It also reuses
independent solvers from the baseline audit on the revised test datasets.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import tempfile
from decimal import Decimal, localcontext
from pathlib import Path

from build_import_package import inspect_steps

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = {int(d["id"]): d["block"] for p in (ROOT / "courses/86957/steps").glob("*/*.step")
          for d in [json.loads(p.read_text(encoding="utf-8"))]}
RECORDS = []


def cases(sid):
    return BLOCKS[sid]["source"]["test_cases"]


def record(sid, name, **values):
    RECORDS.append({"step_id": sid, "check": name, "passed": True, **values})


def checker(sid):
    """Load reviewed grading functions, without executing generate() or solve()."""
    source = ast.parse(BLOCKS[sid]["source"]["code"])
    allowed = []
    for node in source.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module]
            if not all(m in {"math", "decimal", "re", "random"} for m in modules):
                raise ValueError(f"Review additional grader imports before running: {sid}, {modules}")
            allowed.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name not in {"generate", "solve"}:
            allowed.append(node)
        elif isinstance(node, ast.Assign):
            ast.literal_eval(node.value)
            allowed.append(node)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            pass
        elif isinstance(node, ast.FunctionDef):
            pass
        else:
            raise ValueError(f"Review additional grader setup before running: {sid}, {type(node).__name__}")
    namespace = {}
    exec(compile(ast.Module(body=allowed, type_ignores=[]), f"reviewed-checker-{sid}", "exec"), namespace)
    def accepted(reply, clue):
        result = namespace["check"](reply, clue)
        # Stepik also accepts (grade, feedback); a nonempty tuple is not a pass.
        return result[0] if isinstance(result, (tuple, list)) else result
    return accepted


def response_checks():
    for sid in (3262682, 3262692, 3280697, 3280727, 3381234, 4738986):
        fn = checker(sid)
        for index, (_, clue) in enumerate(cases(sid), 1):
            if not fn(clue, clue):
                raise AssertionError((sid, index, "saved reference rejected"))
            if fn("THIS_IS_NOT_AN_ANSWER", clue):
                raise AssertionError((sid, index, "malformed response accepted"))
        record(sid, "references_accepted_and_malformed_responses_rejected", cases=len(cases(sid)))

    fn = checker(3262682)
    _, clue = cases(3262682)[0]
    assert fn("4.333071682\n", clue)
    assert not fn("4.34", clue)
    for bad in ("nan", "inf", "-inf", "4.333071682 0"):
        assert not fn(bad, clue), bad
    record(3262682, "specified_precision_and_negative_controls", accepted="4.333071682", rejected=["4.34", "nan", "inf", "extra token"])

    fn = checker(3262692)
    _, clue = cases(3262692)[2]
    for answer in ("0.28032787010526721269", "0.28032787010526721272"):
        assert fn(answer, clue)
    assert not fn("0.29", clue)
    assert not fn("nan", clue)
    assert not fn("inf", clue)
    record(3262692, "equivalent_formulas_accepted_wrong_value_rejected")

    fn = checker(3280697)
    _, clue = cases(3280697)[4]
    correct = "3000000000 0\n2999999996 2 3"
    old_rounded = "3000000000 0\n3e+09 2 3"
    assert fn(correct, clue)
    assert not fn(old_rounded, clue)
    assert not fn("3000000001 0\n2999999996 2 3", clue)
    assert not fn(correct + " 0", clue)
    assert not fn("3000000000 0\nnan 2 3", clue)
    assert not fn("3000000000 0\ninf 2 3", clue)
    _, tied_clue = cases(3280697)[-2]
    assert fn("0 2 3 5 1", tied_clue)
    assert not fn("0 2 5 3 1", tied_clue)
    record(3280697, "accurate_maximum_accepted_old_rounding_rejected", correct=correct, rejected=old_rounded)

    fn = checker(3280727)
    data, clue = cases(3280727)[1]
    assert list(map(Decimal, data.split())) == [0, 0, 0, 0]
    assert Decimal(clue) == 0 and fn("0\n", clue)
    assert not fn("ERROR", clue)
    record(3280727, "unused_division_branch_returns_zero")

    fn = checker(3381234)
    _, clue = cases(3381234)[0]
    answer = "\n".join(line.rstrip() for line in clue.splitlines())
    assert fn(answer, clue) and fn("\t".join(clue.split()) + "\n", clue)
    wrong = clue.split()
    wrong[0] = str(int(wrong[0]) + 1)
    assert not fn(" ".join(wrong), clue)
    assert not fn(clue + " 0", clue)
    record(3381234, "matrix_whitespace_allowed_wrong_values_and_extra_tokens_rejected")

    fn = checker(4738986)
    _, clue = cases(4738986)[0]
    assert fn(clue + "\n", clue) and fn(clue + "\r\n", clue)
    assert not fn(clue + "0", clue)
    record(4738986, "final_lf_and_crlf_allowed_extra_digit_rejected", scope="Local grader only; live Stepik not exercised")


def verify_constraints_and_references():
    for data, clue in cases(3383209):
        n = int(data)
        assert 0 <= n <= 10**9
        assert int(clue) == n * (n - 1) // 2 + 1
    record(3383209, "extension_cords_independent_formula", cases=len(cases(3383209)))

    for data, _ in cases(3281353):
        w, h, x1, y1, x2, y2, sw, sh = map(int, data.split())
        assert 0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h
        assert sw > 0 and sh > 0
    record(3281353, "rectangle_corner_order_and_bounds", cases=len(cases(3281353)))

    for data, clue in cases(3446094):
        assert all("a" <= ch <= "z" for ch in data.strip())
    record(3446094, "test_alphabet_matches_lowercase_constraint", cases=len(cases(3446094)))

    for data, clue in cases(5850209):
        assert "IiTP" not in data and "IiTP" not in clue
    record(5850209, "corrected_yaml_key_in_input_and_reference", cases=len(cases(5850209)))

    def count_fixed(length, assignments, modulus):
        fixed = {}
        for offset, word in assignments:
            if offset < 0 or offset + len(word) > length:
                return 0
            for i, ch in enumerate(word, offset):
                if i in fixed and fixed[i] != ch:
                    return 0
                fixed[i] = ch
        return pow(26, length - len(fixed), modulus)

    datasets = subcases = 0
    for data, clue in cases(3446002):
        datasets += 1
        lines = data.splitlines()
        total = int(lines[0])
        assert len(lines) == 1 + 3 * total
        answers = []
        for i in range(total):
            length, modulus = map(int, lines[1 + 3 * i].split())
            a, b = lines[2 + 3 * i].strip(), lines[3 + 3 * i].strip()
            assert 1 <= length <= 10**9 and 1 <= modulus <= 10**4
            assert 1 <= len(a) <= 200 and 1 <= len(b) <= 200
            assert all("a" <= ch <= "z" for ch in a + b)
            ab = [(0, a), (length - len(b), b)]
            ba = [(0, b), (length - len(a), a)]
            answers.append(str((count_fixed(length, ab, modulus) + count_fixed(length, ba, modulus)
                                - count_fixed(length, ab + ba, modulus)) % modulus))
            subcases += 1
        assert answers == clue.split(), (data[:100], answers, clue)
    record(3446002, "linewise_input_constraints_and_independent_inclusion_exclusion", datasets=datasets, subcases=subcases)

    path = ROOT / "audit/checks/verify_export_checks.py"
    spec = importlib.util.spec_from_file_location("baseline_reference_solvers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for sid, block in BLOCKS.items():
        module.STEPS[sid]["block"] = block
    module.RESULTS = []
    module.verify_reference_answers()
    for result in module.RESULTS:
        assert not result["mismatches"], result
    record(None, "independent_reference_solvers_on_revised_datasets",
           tasks=len(module.RESULTS), cases=sum(r["cases"] for r in module.RESULTS), results=module.RESULTS)


def numeric_cpp_solutions():
    source = ROOT / "imports/86957/validation/numeric_solutions.cpp"
    version = subprocess.run(["g++", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    with tempfile.TemporaryDirectory(prefix="stepik-numeric-", dir=ROOT / "imports/86957") as tmp:
        binary = Path(tmp) / "numeric-solutions"
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-pedantic-errors",
                        "-O2", str(source), "-o", str(binary)], check=True, capture_output=True, text=True, timeout=30)
        results = []
        for sid in (3262682, 3262692, 3264622, 3280697, 3280727, 3281353):
            fn = checker(sid)
            for index, (data, clue) in enumerate(cases(sid), 1):
                run = subprocess.run([str(binary), str(sid)], input=data, text=True,
                                     capture_output=True, check=True, timeout=3)
                if not fn(run.stdout, clue):
                    raise AssertionError((sid, index, run.stdout, clue))
            results.append({"step_id": sid, "test_cases_passed": len(cases(sid))})
    record(None, "independent_cpp_numeric_solutions", compiler=version, standard="c++17",
           tasks=len(results), cases=sum(r["test_cases_passed"] for r in results), results=results)


def main():
    _, changed, checks = inspect_steps(ROOT, 86957)
    response_checks()
    verify_constraints_and_references()
    numeric_cpp_solutions()
    result = {"course_id": 86957, "scope": "Local regression checks of edited .step files; not live Stepik",
        "all_passed": True, "changed_steps": len(changed), "structural_checks": checks,
        "checks": RECORDS, "check_count": len(RECORDS),
        "revised_file_sha256": {s["repository_path"]: s["file_sha256"] for s in changed}}
    output = ROOT / "imports/86957/validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": True, "check_count": len(RECORDS),
        "changed_steps": len(changed), "output": str(output.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
