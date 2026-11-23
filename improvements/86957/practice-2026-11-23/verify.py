#!/usr/bin/env python3
"""Reproduce the local verification of four module-10 assessment replacements.

This does not submit code to Stepik or reproduce its compiler/container limits.
--testdata writes exact UTF-8 .in/.out files plus their SHA256 index for review.
"""

import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
TASKS = {
    "4734985": {
        "path": "steps/770595/11_4734985_code.step",
        "grader": "graders/stable_records.py",
        "references": ["examples/stable_records.cpp", "examples/stable_records_index.cpp"],
    },
    "3496826": {
        "path": "steps/771129/07_3496826_code.step",
        "grader": "graders/first_index.py",
        "references": ["examples/first_index.cpp", "examples/first_index_manual.cpp"],
    },
}
CHOICES = {
    "3408767": "steps/770595/09_3408767_choice.step",
    "3408864": "steps/771129/05_3408864_choice.step",
}
FLAGS = ["-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror"]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def changed_fields(left, right, prefix=""):
    if type(left) is not type(right):
        return [prefix]
    if isinstance(left, dict):
        result = []
        for key in sorted(set(left) | set(right)):
            pointer = prefix + "/" + key.replace("~", "~0").replace("/", "~1")
            result.extend([pointer] if key not in left or key not in right
                          else changed_fields(left[key], right[key], pointer))
        return result
    if isinstance(left, list):
        if len(left) != len(right):
            return [prefix]
        return [path for i, (a, b) in enumerate(zip(left, right))
                for path in changed_fields(a, b, prefix + "/" + str(i))]
    return [] if left == right else [prefix]


def metadata_checks(baseline, report):
    journal = read_json(PACKAGE / "changes_practice.json")
    entries = {str(item["step_id"]): item for item in journal["changes"]}
    require(set(entries) == set(TASKS) | set(CHOICES), "Journal must contain exactly these four steps")
    for step_id, entry in entries.items():
        relative = Path(entry["path"])
        old_path = baseline / relative.relative_to("steps")
        new_path = PACKAGE / relative
        old, new = read_json(old_path), read_json(new_path)
        require(str(old["id"]) == str(new["id"]) == step_id, "ID changed: " + step_id)
        require(old["time"] == new["time"], "Export time changed: " + step_id)
        require(old["block"]["name"] == new["block"]["name"], "Block type changed")
        require(changed_fields(old, new) == entry["changed_fields"], "Changed-field journal mismatch: " + step_id)
        require(digest(old_path.read_bytes()) == entry["baseline_sha256"], "Baseline hash mismatch: " + step_id)
        require(digest(new_path.read_bytes()) == entry["prepared_sha256"], "Prepared hash mismatch: " + step_id)
        block, old_block = new["block"], old["block"]
        if step_id in TASKS:
            for name, value in old_block["source"].items():
                if name not in ("code", "test_cases"):
                    require(block["source"][name] == value, "Code source setting changed: " + name)
            for name, value in old_block["options"].items():
                if name != "samples":
                    require(block["options"][name] == value, "Code option changed: " + name)
            require(block["source"]["test_cases"] == [], "Static tests must be empty; generate owns all cases")
            require(block["source"]["test_archive"] == [], "Unexpected archive tests")
            require(block["tests_archive"] == old_block["tests_archive"], "Existing archive endpoint changed")
            require(block["source"]["code"] == (PACKAGE / TASKS[step_id]["grader"]).read_text(),
                    "Embedded and standalone grader differ: " + step_id)
        else:
            source = block["source"]
            for name, value in old_block["source"].items():
                if name not in ("options", "is_options_feedback"):
                    require(source[name] == value, "Choice setting changed: " + name)
            require(block["options"] == old_block["options"], "Choice options flags changed")
            require(len(source["options"]) == 10 == source["sample_size"], "Choice count mismatch")
            require(source["is_options_feedback"] is True, "Per-option feedback disabled")
            correct = [i for i, option in enumerate(source["options"], 1) if option["is_correct"]]
            require(correct == entry["correct_option_numbers_in_source_order"], "Choice answer key mismatch")
            require(len(correct) == 5, "Expected five true and five false assertions")
            require(all(option["feedback"].strip() for option in source["options"]), "Missing feedback")
        report["metadata"].append({"step_id": step_id, "status": "passed", "changed_fields": entry["changed_fields"]})


def independent_answer(step_id, dataset):
    numbers = list(map(int, dataset.split()))
    if step_id == "4734985":
        n = numbers[0]
        require(0 <= n <= 100000 and len(numbers) == 1 + 2 * n, "Invalid record input")
        require(all(-1000000000 <= x <= 1000000000 for x in numbers[1:]), "Record outside bounds")
        groups = defaultdict(list)
        original = list(zip(numbers[1::2], numbers[2::2]))
        for key, label in original:
            groups[key].append(label)
        result = [(key, label) for key in sorted(groups) for label in groups[key]]
        require(Counter(original) == Counter(result), "Independent oracle lost records")
        return [value for record in result for value in record]
    n, q = numbers[:2]
    require(0 <= n <= 100000 and 0 <= q <= 100000, "Search lengths outside bounds")
    require(len(numbers) == 2 + n + q, "Search token count mismatch")
    values, queries = numbers[2:2 + n], numbers[2 + n:]
    require(all(-1000000000 <= x <= 1000000000 for x in values + queries), "Search value outside bounds")
    require(all(a <= b for a, b in zip(values, values[1:])), "Unsorted search input")
    result = []
    for key in queries:
        index = bisect_left(values, key)
        result.append(index if index < n and values[index] == key else -1)
    return result


def checker_probes(check, answer):
    tokens = answer.split()
    require(check(answer, answer) is True, "Checker rejects exact answer")
    require(check("\n\t" + " \t\n".join(tokens) + "\n", answer) is True, "Checker rejects valid whitespace")
    require(check(answer + "\n123456789\n", answer) is False, "Checker accepts extra token")
    if tokens:
        require(check(" ".join(tokens[1:]), answer) is False, "Checker accepts missing token")
        wrong = [str(int(tokens[0]) + 1)] + tokens[1:]
        require(check(" ".join(wrong), answer) is False, "Checker accepts altered value")
        wrong[0] = tokens[0] + ".0"
        require(check(" ".join(wrong), answer) is False, "Checker accepts floating-point syntax")
        value = int(tokens[0])
        alternative = ("-" if value < 0 else "+") + "00" + str(abs(value))
        require(check(" ".join([alternative] + tokens[1:]), answer) is True, "Checker rejects integer spelling")
    else:
        require(check("0", answer) is False, "Checker accepts number for empty output")
    return 7 if tokens else 4


def materialize(testdata):
    """Executed in a separate subprocess with a timeout by the parent verifier."""
    expected = read_json(PACKAGE / "cases.json")["tasks"]
    index = {"schema_version": 1, "status": "running", "all_passed": False,
             "scope": "Local cases generated from embedded Stepik source.code", "tasks": {},
             "checker_probes": 0}
    save_json(testdata / "index.json", index)
    try:
        for step_id, task in TASKS.items():
            block = read_json(PACKAGE / task["path"])["block"]
            namespace = {"__name__": "local_stepik_source_" + step_id}
            exec(compile(block["source"]["code"], task["path"] + "::source.code", "exec"), namespace)
            tests = namespace["generate"]()
            require(tests == namespace["generate"](), "Non-deterministic generator: " + step_id)
            specs = list(namespace["case_specs"]())
            require(0 < len(tests) <= 100 and len(tests) == len(specs), "Invalid generated case count")
            require(len(tests) == len(expected[step_id]["cases"]), "Catalog count mismatch")
            require(block["options"]["samples"] == [list(t) for t in tests[:block["source"]["samples_count"]]],
                    "Displayed samples disagree with generated cases")
            cases = []
            for number, ((name, data, tags), pair) in enumerate(zip(specs, tests), 1):
                require(len(pair) == 2 and all(isinstance(v, str) for v in pair), "Invalid dataset/clue pair")
                dataset, answer = pair
                require(dataset == data and dataset.endswith("\n"), "Fixture data mismatch")
                require(namespace["solve"](dataset) == answer, "solve disagrees with clue")
                require(list(map(int, answer.split())) == independent_answer(step_id, dataset),
                        "Independent oracle disagrees: " + name)
                index["checker_probes"] += checker_probes(namespace["check"], answer)
                case = {"number": number, "name": name,
                        "sample": number <= block["source"]["samples_count"], "tags": tags,
                        "input_sha256": digest(dataset.encode()), "answer_sha256": digest(answer.encode()),
                        "input_bytes": len(dataset.encode()), "answer_bytes": len(answer.encode())}
                require(case == expected[step_id]["cases"][number - 1], "Catalog hash/metadata mismatch: " + name)
                prefix = Path(step_id) / ("{:03d}_".format(number) + name)
                for extension, content in ((".in", dataset), (".out", answer)):
                    path = testdata / prefix.with_suffix(extension)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8")
                case["input_file"] = prefix.with_suffix(".in").as_posix()
                case["answer_file"] = prefix.with_suffix(".out").as_posix()
                cases.append(case)
            index["tasks"][step_id] = {"status": "passed", "cases": cases}
        index["status"] = "passed"
        index["all_passed"] = True
        save_json(testdata / "index.json", index)
    except BaseException as error:
        index["status"] = "failed"
        index["error"] = type(error).__name__ + ": " + str(error)
        save_json(testdata / "index.json", index)
        raise


def execute(command, timeout, data=None):
    started = time.perf_counter()
    completed = subprocess.run(command, input=data, text=True, capture_output=True, timeout=timeout, check=False)
    if completed.returncode != 0:
        raise RuntimeError("Command failed ({}): {}\n{}".format(
            completed.returncode, " ".join(map(str, command)), completed.stderr[-4000:]))
    return completed.stdout, time.perf_counter() - started


def mutations():
    stable = (PACKAGE / "examples/stable_records.cpp").read_text()
    index = (PACKAGE / "examples/stable_records_index.cpp").read_text()
    search = (PACKAGE / "examples/first_index_manual.cpp").read_text()
    sort_loop = "    for (const Record& record : records) {\n"
    drop_keys = stable.replace(sort_loop,
        "    bool have_last = false;\n    int last_key = 0;\n" + sort_loop +
        "        if (have_last && record.priority == last_key) { continue; }\n"
        "        have_last = true;\n        last_key = record.priority;\n")
    drop_records = stable.replace("#include <vector>", "#include <vector>\n#include <set>\n#include <utility>")
    drop_records = drop_records.replace(sort_loop,
        "    std::set<std::pair<int, int>> seen;\n" + sort_loop +
        "        if (!seen.insert({record.priority, record.label}).second) { continue; }\n")
    last = search.replace("values[static_cast<std::size_t>(middle)] < key",
                          "values[static_cast<std::size_t>(middle)] <= key")
    last = last.replace("    if (left == static_cast<int>(values.size()) ||",
                        "    if (left == 0) { return -1; }\n    --left;\n    if (left == static_cast<int>(values.size()) ||")
    any_match = search.replace("        if (values[static_cast<std::size_t>(middle)] < key) {",
        "        if (values[static_cast<std::size_t>(middle)] == key) { return middle; }\n"
        "        if (values[static_cast<std::size_t>(middle)] < key) {")
    final_guard = ("    if (left == static_cast<int>(values.size()) ||\n"
                   "        values[static_cast<std::size_t>(left)] != key) {\n"
                   "        return -1;\n    }\n")
    return [
        ("4734985", "drops_equal_keys", drop_keys),
        ("4734985", "drops_identical_records", drop_records),
        ("4734985", "reverses_equal_keys", index.replace("left.original_index < right.original_index", "left.original_index > right.original_index")),
        ("4734985", "sorts_by_label", index.replace("left.original_index < right.original_index", "left.label < right.label")),
        ("4734985", "descending_priority", stable.replace("left.priority < right.priority", "left.priority > right.priority")),
        ("3496826", "last_occurrence", last),
        ("3496826", "any_occurrence", any_match),
        ("3496826", "one_based_index", search.replace("    return left;", "    return left + 1;")),
        ("3496826", "insertion_position_for_absent", search.replace(final_guard, "")),
        ("3496826", "empty_returns_zero", search.replace("    int left = 0;", "    if (values.empty()) { return 0; }\n    int left = 0;")),
        ("3496826", "absent_returns_zero", search.replace("        return -1;", "        return 0;")),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=PACKAGE / "baseline/steps")
    parser.add_argument("--report", type=Path, default=PACKAGE / "validation.json")
    parser.add_argument("--testdata", type=Path, help="Keep exact generated .in/.out files and SHA256 index")
    parser.add_argument("--compiler", default="g++")
    parser.add_argument("--compile-timeout", type=float, default=45)
    parser.add_argument("--generation-timeout", type=float, default=45)
    parser.add_argument("--case-timeout", type=float, default=5)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        require(args.testdata is not None, "Worker needs --testdata")
        materialize(args.testdata)
        return 0
    report = {
        "schema_version": 1, "status": "running", "all_passed": False,
        "scope": "Local schema, generated tests, checkers, C++ references and mutation checks for four module-10 steps",
        "live_stepik_verified": False,
        "limits_note": "Local wall-clock safeguards only; Stepik compiler, grading, time and memory containers were not reproduced.",
        "started_at": utc_now(), "metadata": [], "references": [], "mutations": [],
        "timeouts_seconds": {"compile": args.compile_timeout, "generate": args.generation_timeout, "case": args.case_timeout},
        "input_sha256": {},
        "input_hash_paths": "Relative paths are relative to this package; baseline paths are absolute.",
        "counts": {"compilations": 0, "runtime_cases": 0, "reference_cases": 0,
                   "negative_probes": 0, "generated_cases": 0, "checker_probes": 0},
    }
    save_json(args.report, report)  # Invalidate any old success before running checks.
    try:
        require(all(value > 0 for value in (args.compile_timeout, args.generation_timeout, args.case_timeout)),
                "Timeouts must be positive")
        relevant = ["verify.py", "changes_practice.json", "cases.json"] + list(CHOICES.values())
        for task in TASKS.values():
            relevant += [task["path"], task["grader"]] + task["references"]
        input_paths = {name: PACKAGE / name for name in sorted(relevant)}
        for entry in read_json(PACKAGE / "changes_practice.json")["changes"]:
            baseline_path = (args.baseline / Path(entry["path"]).relative_to("steps")).resolve()
            input_paths[str(baseline_path)] = baseline_path
        report["input_sha256"] = {name: digest(path.read_bytes()) for name, path in input_paths.items()}
        report["environment"] = {"python": sys.version.split()[0], "platform": platform.platform(),
                                 "compiler": execute([args.compiler, "--version"], args.compile_timeout)[0].splitlines()[0]}
        metadata_checks(args.baseline.resolve(), report)
        save_json(args.report, report)
        with tempfile.TemporaryDirectory(prefix="practice-verification-", dir=REPO.parent) as folder:
            work = Path(folder)
            testdata = args.testdata.resolve() if args.testdata else work / "testdata"
            execute([sys.executable, str(Path(__file__).resolve()), "--worker", "--testdata", str(testdata)],
                    args.generation_timeout)
            fixtures = read_json(testdata / "index.json")
            require(fixtures["all_passed"] and fixtures["status"] == "passed", "Fixture worker failed")
            report["testdata"] = fixtures
            report["testdata"]["retained_directory"] = str(testdata) if args.testdata else None
            report["counts"]["generated_cases"] = sum(len(task["cases"]) for task in fixtures["tasks"].values())
            report["counts"]["checker_probes"] = fixtures["checker_probes"]
            checkers = {}
            for step_id, task in TASKS.items():
                namespace = {}
                exec(compile(read_json(PACKAGE / task["path"])["block"]["source"]["code"], task["path"], "exec"), namespace)
                checkers[step_id] = namespace["check"]
                cases = fixtures["tasks"][step_id]["cases"]
                for reference in task["references"]:
                    for standard in ("c++17", "c++20"):
                        binary = work / (Path(reference).stem + "-" + standard)
                        command = [args.compiler, "-std=" + standard] + FLAGS + [str(PACKAGE / reference), "-o", str(binary)]
                        execute(command, args.compile_timeout)
                        report["counts"]["compilations"] += 1
                        maximum = 0.0
                        for case in cases:
                            data = (testdata / case["input_file"]).read_text()
                            expected = (testdata / case["answer_file"]).read_text()
                            actual, seconds = execute([str(binary)], args.case_timeout, data)
                            report["counts"]["runtime_cases"] += 1
                            report["counts"]["reference_cases"] += 1
                            require(checkers[step_id](actual, expected) is True,
                                    "Reference failed: {}/{} on {}".format(reference, standard, case["name"]))
                            maximum = max(maximum, seconds)
                        report["references"].append({"source": reference, "step_id": step_id,
                            "standard": standard, "flags": FLAGS, "cases_passed": len(cases),
                            "status": "passed", "max_local_wall_seconds": round(maximum, 6)})
                        save_json(args.report, report)
            for step_id, name, code in mutations():
                source, binary = work / (name + ".cpp"), work / name
                source.write_text(code)
                execute([args.compiler, "-std=c++17"] + FLAGS + [str(source), "-o", str(binary)], args.compile_timeout)
                report["counts"]["compilations"] += 1
                witness = None
                for case in fixtures["tasks"][step_id]["cases"]:
                    if case["sample"]:
                        continue  # Require a hidden-case witness, not just a public sample.
                    data = (testdata / case["input_file"]).read_text()
                    expected = (testdata / case["answer_file"]).read_text()
                    actual, _ = execute([str(binary)], args.case_timeout, data)
                    report["counts"]["runtime_cases"] += 1
                    if not checkers[step_id](actual, expected):
                        witness = {"name": case["name"], "number": case["number"], "sample": False,
                                   "input_sha256": case["input_sha256"]}
                        break
                require(witness is not None, "Incorrect solution survived all cases: " + name)
                report["mutations"].append({"step_id": step_id, "name": name, "status": "rejected",
                                             "source_sha256": digest(code.encode()), "witness": witness})
                report["counts"]["negative_probes"] += 1
                save_json(args.report, report)
        final_hashes = {name: digest(path.read_bytes()) for name, path in input_paths.items()}
        require(final_hashes == report["input_sha256"], "Verification inputs changed during the run")
        report["inputs_unchanged_after_run"] = True
        report["status"] = "passed"
        report["all_passed"] = True
        report["completed_at"] = utc_now()
        save_json(args.report, report)
        print("PASS: {} assessed steps; {} generated cases; {} C++17/20 reference runs; {} incorrect solutions rejected.".format(
            len(report["metadata"]), report["counts"]["generated_cases"],
            report["counts"]["reference_cases"], report["counts"]["negative_probes"]))
        print("Report: " + str(args.report))
        return 0
    except BaseException as error:
        report["status"] = "failed"
        report["all_passed"] = False
        report["completed_at"] = utc_now()
        report["error"] = type(error).__name__ + ": " + str(error)
        save_json(args.report, report)
        print(report["error"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
