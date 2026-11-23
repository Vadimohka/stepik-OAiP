#!/usr/bin/env python3
"""Validate author blocks and the demonstrated C++ answer, without Stepik access.

The exhaustive truth tables check the stored answer keys against independently
specified editorial keys. They are not an implementation of Stepik grading.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
EXPECTED_KEYS = {
    4718246: {1},
    3437886: {1, 2, 4, 6, 7},
    3424087: {1, 4, 6, 9},
    3437952: {1, 3, 7, 8, 10},
}


class Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def plain(value: str) -> str:
    parser = Text()
    parser.feed(value)
    return " ".join("".join(parser.parts).split())


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def fixed_fields(step: dict) -> dict:
    """Remove only the fields this editorial package is allowed to modify."""
    result = copy.deepcopy(step)
    block = result["block"]
    for name in ("text", "feedback_correct", "feedback_wrong"):
        block.pop(name, None)
    block["source"].pop("is_options_feedback", None)
    for option in block["source"]["options"]:
        for name in ("text", "is_correct", "feedback"):
            option.pop(name, None)
    return result


def validate(args: argparse.Namespace) -> dict:
    input_hashes: dict[str, str] = {}

    def read_input(path: Path) -> bytes:
        data = path.read_bytes()
        key = path.resolve().relative_to(REPO).as_posix()
        checksum = hashlib.sha256(data).hexdigest()
        check(key not in input_hashes or input_hashes[key] == checksum, f"Input changed during verification: {key}")
        input_hashes[key] = checksum
        return data

    read_input(Path(__file__))
    manifest = json.loads(read_input(PACKAGE / "changes_assessment.json"))
    entries = manifest["changes"]
    check({entry["step_id"] for entry in entries} == set(EXPECTED_KEYS), "Unexpected assessment IDs")
    check(len(entries) == 4, "Expected exactly four assessments")
    check(len(list((PACKAGE / "steps").glob("*/*.step"))) == 4, "Unlisted assessment files")
    contexts = {}
    revised_context_ids = {3215112, 3215113, 3215200, 3215206, 3580923}
    required_context_ids = {sid for entry in entries for rationale in entry["rationales"]
                            for sid in rationale["context_step_ids"]}
    for sid in required_context_ids:
        directory = args.context if sid in revised_context_ids else REPO / "courses/86957/steps"
        matching = list(directory.glob(f"*/*_{sid}_text.step"))
        check(len(matching) == 1, f"Required context {sid} must occur exactly once in {directory}")
        contexts[sid] = json.loads(read_input(matching[0]))
    check(revised_context_ids.issubset(contexts), "The revised file-I/O lessons must be present")

    reports = []
    total_subsets = 0
    total_permuted_subsets = 0
    total_context_checks = 0
    for entry in entries:
        step_id = entry["step_id"]
        relative = Path(entry["path"])
        check(relative.parts[0] == "steps" and ".." not in relative.parts, "Invalid package path")
        revised = json.loads(read_input(PACKAGE / relative))
        old_path = args.baseline / Path(*relative.parts[1:])
        original = json.loads(read_input(old_path))
        check(int(revised["id"]) == step_id, f"Wrong ID in {relative}")
        check(fixed_fields(revised) == fixed_fields(original), f"Protected fields changed: {step_id}")
        source = revised["block"]["source"]
        options = source["options"]
        n = len(options)
        check(source["sample_size"] == n, f"Question {step_id} must show all its preserved options")
        check(source["is_options_feedback"] is True, f"Feedback disabled: {step_id}")
        check(source["is_multiple_choice"] == revised["block"]["options"]["is_multiple_choice"],
              f"Conflicting choice modes: {step_id}")
        check(set(entry["correct_options"]) == EXPECTED_KEYS[step_id], f"Editorial key changed: {step_id}")
        check(len(entry["rationales"]) == n, f"Missing rationales: {step_id}")
        texts = [plain(option["text"]) for option in options]
        check(len(set(texts)) == n, f"Duplicate options: {step_id}")
        for index, (option, rationale) in enumerate(zip(options, entry["rationales"]), 1):
            check(type(option["is_correct"]) is bool, f"Non-boolean key: {step_id}/{index}")
            check(bool(plain(option["feedback"])), f"Empty option feedback: {step_id}/{index}")
            check(rationale["option"] == index and rationale["is_correct"] is option["is_correct"],
                  f"Rationale does not match option: {step_id}/{index}")
            check(rationale["explanation"] == option["feedback"], f"Feedback differs from rationale: {step_id}/{index}")
            check(not re.search(r"вс[её] перечислен|ничего из перечислен|вариант[ыа]? (?:выше|ниже)", texts[index - 1], re.I),
                  f"Order-dependent option: {step_id}/{index}")
            supporting_text = " ".join(plain(contexts[s]["block"]["text"]) for s in rationale["context_step_ids"])
            evidence = " ".join(rationale["context_evidence"].split())
            check(evidence in supporting_text, f"Context evidence missing: {step_id}/{index}: {evidence}")
            total_context_checks += 1

        # All answer subsets, including invalid multiple selections for a
        # single-choice question, must agree with the editorial truth table.
        permutations = [list(range(n)), list(reversed(range(n))), list(range(1, n)) + [0]]
        for order_index, order in enumerate(permutations):
            for mask in range(1 << n):
                selected_original_positions = {order[i] + 1 for i in range(n) if mask & (1 << i)}
                expected = selected_original_positions == EXPECTED_KEYS[step_id]
                agrees_with_stored_key = all(
                    bool(mask & (1 << displayed)) == options[original_index]["is_correct"]
                    for displayed, original_index in enumerate(order)
                )
                check(expected == agrees_with_stored_key, f"Truth-table mismatch: {step_id}, mask {mask}")
                if order_index == 0:
                    total_subsets += 1
                else:
                    total_permuted_subsets += 1
        reports.append({"step_id": step_id, "options": n, "correct_options": sorted(EXPECTED_KEYS[step_id]),
                        "protected_fields": "preserved", "local_subsets": 1 << n})

    move_step = json.loads(read_input(PACKAGE / "steps/853535/04_4718246_choice.step"))
    embedded = re.search(r'<pre><code class="language-cpp">(.*?)</code></pre>', move_step["block"]["text"], re.S)
    check(embedded is not None, "Missing demonstrated C++ source")
    source_file = PACKAGE / "examples/move_const_vector.cpp"
    check(html.unescape(embedded.group(1)) == read_input(source_file).decode("utf-8"),
          "Tested C++ file differs from the question")
    compiler_version = subprocess.run([args.cxx, "--version"], check=True, capture_output=True, text=True).stdout.splitlines()[0]
    compilations = []
    with tempfile.TemporaryDirectory(prefix="assessment-check-", dir=PACKAGE) as temporary:
        for standard in ("c++17", "c++20"):
            binary = Path(temporary) / standard
            command = [args.cxx, f"-std={standard}", "-Wall", "-Wextra", "-Wpedantic", "-Werror", str(source_file), "-o", str(binary)]
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
            run = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=10)
            check(run.stdout == "4 1\n" and run.stderr == "", f"Unexpected C++ result for {standard}")
            compilations.append({"standard": standard, "warnings_as_errors": True, "stdout": run.stdout, "exit_code": run.returncode})

    for relative, checksum in input_hashes.items():
        check(hashlib.sha256((REPO / relative).read_bytes()).hexdigest() == checksum,
              f"Input changed during verification: {relative}")
    return {"status": "passed", "all_passed": True,
            "input_sha256": dict(sorted(input_hashes.items())),
            "scope": "local author-block validation only; not Stepik grading or publication",
            "assessments": reports, "local_truth_table_subsets": total_subsets,
            "permuted_truth_table_subsets": total_permuted_subsets, "context_evidence_checks": total_context_checks,
            "compiler": compiler_version, "cpp_example": compilations}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=PACKAGE / "baseline")
    parser.add_argument("--context", type=Path, default=REPO / "improvements/86957/quality-2026-11-23/steps")
    parser.add_argument("--cxx", default="g++")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.report:
        args.report.write_text(json.dumps({"status": "running", "all_passed": False}) + "\n", encoding="utf-8")
    try:
        result = validate(args)
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        result = {"status": "failed", "all_passed": False, "error": str(error)}
        if args.report:
            args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return 1
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
