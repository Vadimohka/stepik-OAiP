#!/usr/bin/env python3
"""Verify all stored YAML->INI answers and the format-sensitive checker.

The independent converter validates the restricted input language stated in the
step. It does not use a general YAML parser, the stored answer or checker logic.
Run from any directory. No network or third-party packages are required.
"""
import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
RELATIVE_STEP = Path("steps/1409621/01_5850209_code.step")
IDENTIFIER = re.compile(r"[a-z]{1,10}")


def convert(dataset):
    lines = dataset.splitlines()
    count = int(lines[0])
    assert 1 <= count <= 50_000
    assert len(dataset.encode("utf-8")) <= 1_000_000
    position = 1
    files = []
    pairs = 0
    max_depth = 0
    for _ in range(count):
        size = int(lines[position])
        position += 1
        assert 1 <= size <= 100_000
        stack = [{"names": set(), "pairs": 0, "path": ()}]
        records = []
        for line in lines[position:position + size]:
            assert "\t" not in line
            indent = len(line) - len(line.lstrip(" "))
            assert indent % 4 == 0
            depth = indent // 4
            max_depth = max(max_depth, depth)
            while len(stack) > depth + 1:
                node = stack.pop()
                assert node["pairs"] > 0, "Empty dictionary"
                stack[-1]["pairs"] += node["pairs"]
            assert len(stack) == depth + 1, "Invalid indentation jump"
            key, value = line[indent:].split(":", 1)
            assert IDENTIFIER.fullmatch(key), repr(key)
            node = stack[-1]
            assert key not in node["names"], "Duplicate dictionary member"
            node["names"].add(key)
            if value:
                assert value.startswith(" ") and IDENTIFIER.fullmatch(value[1:])
                node["pairs"] += 1
                records.append((node["path"], f"{key} = {value[1:]}"))
                pairs += 1
            else:
                stack.append({"names": set(), "pairs": 0,
                              "path": node["path"] + (key,)})
        position += size
        while len(stack) > 1:
            node = stack.pop()
            assert node["pairs"] > 0, "Empty dictionary"
            stack[-1]["pairs"] += node["pairs"]
        assert stack[0]["pairs"] > 0
        output = []
        previous_path = None
        for path, pair in records:
            if path != previous_path:
                if output:
                    output.append("")
                if path:
                    output.append("[" + ".".join(path) + "]")
                previous_path = path
            output.append(pair)
        files.append("\n".join(output))
    assert position == len(lines), "Unconsumed input"
    output = "\n\n".join(files) + "\n\n"
    assert len(output.encode("utf-8")) <= 1_000_000
    return output, {"files": count, "pairs": pairs, "max_depth": max_depth}


def load_check(source):
    tree = ast.parse(source)
    assert all(isinstance(node, ast.FunctionDef) for node in tree.body)
    assert {node.name for node in tree.body} <= {"generate", "check"}
    # These two small checker bodies were reviewed before execution.
    namespace = {}
    exec(compile(tree, "<reviewed YAML checker>", "exec"), namespace)
    return namespace["check"]


def main():
    original = json.loads((ROOT / "courses/86957" / RELATIVE_STEP).read_text())
    revised = json.loads((ROOT / "corrections/86957" / RELATIVE_STEP).read_text())
    before = original["block"]["source"]
    after = revised["block"]["source"]
    assert before["test_cases"] == after["test_cases"], "Existing tests changed"
    old_check = load_check(before["code"])
    new_check = load_check(after["code"])
    rows = []
    positive_count = negative_count = old_false_positives = 0
    for index, (dataset, clue) in enumerate(after["test_cases"]):
        expected, dimensions = convert(dataset)
        assert expected.rstrip("\n") == clue.rstrip("\n"), index
        body = expected.rstrip("\n")
        valid = [body, body + "\n", expected, expected + "\n\n",
                 expected.replace("\n", "\r\n")]
        for answer in valid:
            assert new_check(answer, clue) is True, (index, repr(answer[-30:]))
            positive_count += 1
        invalid = {
            "leading_space": " " + expected,
            "leading_blank_line": "\n" + expected,
            "trailing_space": body + " \n",
            "trailing_tab": body + "\t\n",
            "wrong_separator": expected.replace(" = ", "=", 1),
            "extra_output": expected + "x = y\n",
            "wrong_value": expected.replace(" = ", " = z", 1),
        }
        if "\n\n" in body:
            invalid["missing_internal_blank"] = body.replace("\n\n", "\n", 1)
            invalid["extra_internal_blank"] = body.replace("\n\n", "\n\n\n", 1)
        for label, answer in invalid.items():
            assert new_check(answer, clue) is False, (index, label)
            negative_count += 1
            if old_check(answer, clue):
                old_false_positives += 1
        rows.append({"test_index": index, **dimensions,
                     "stored_answer_matches_reference": True})
    assert old_false_positives == 4 * len(rows)
    report = {
        "step_id": 5850209,
        "status": "passed",
        "stored_test_cases": len(rows),
        "positive_checker_cases": positive_count,
        "negative_checker_cases": negative_count,
        "old_checker_false_positives_rejected_now": old_false_positives,
        "reference": "Independent restricted-YAML parser and INI formatter",
        "live_stepik_execution": False,
        "test_cases": rows,
    }
    destination = Path(__file__).with_name("results.json")
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "test_cases"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
