#!/usr/bin/env python3
"""Check function lessons, exact HTML examples and their executable contracts."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
FLAGS = ["-Wall", "-Wextra", "-Wpedantic", "-Werror", "-O2", "-DNDEBUG"]


class CppBlocks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.current: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = dict(attrs).get("class") or ""
        if tag == "code" and "language-cpp" in classes.split():
            if self.current is not None:
                raise ValueError("Nested C++ code block")
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "code" and self.current is not None:
            self.blocks.append("".join(self.current))
            self.current = None


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def inputs() -> dict[str, str]:
    files = [HERE / "verify.py", HERE / "cases.json", HERE / "changes_functions.json"]
    files += sorted((HERE / "steps").glob("*/*.step"))
    files += sorted((HERE / "baseline" / "steps").glob("*/*.step"))
    files += sorted((HERE / "examples").glob("*.cpp"))
    return {
        path.relative_to(HERE).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
    }


def non_text_fields(data: dict) -> dict:
    result = deepcopy(data)
    result["block"].pop("text")
    return result


def check_materials(specifications: list[dict]) -> list[dict]:
    steps: dict[int, tuple[Path, dict]] = {}
    for path in sorted((HERE / "steps").glob("*/*.step")):
        step = json.loads(path.read_text(encoding="utf-8"))
        step_id = int(step["id"])
        if step_id in steps:
            raise ValueError(f"Duplicate step: {step_id}")
        if step["block"]["name"] != "text":
            raise ValueError(f"Non-text step: {step_id}")
        relative = path.relative_to(HERE / "steps")
        baseline = HERE / "baseline" / "steps" / relative
        if not baseline.is_file():
            if (HERE / "manifest.json").is_file():
                raise ValueError(f"Manifest package is missing its baseline: {relative}")
            baseline = HERE.parents[2] / "courses" / "86957" / "steps" / relative
        before = json.loads(baseline.read_text(encoding="utf-8"))
        if non_text_fields(step) != non_text_fields(before):
            raise ValueError(f"Fields other than block.text changed: {relative}")
        steps[step_id] = (path, step)

    changes = json.loads((HERE / "changes_functions.json").read_text(encoding="utf-8"))["changes"]
    changed_ids = [int(change["step_id"]) for change in changes]
    if len(set(changed_ids)) != len(changed_ids) or set(changed_ids) != set(steps):
        raise ValueError("The change log must cover every prepared step exactly once")

    expected: dict[int, list[str]] = defaultdict(list)
    sources: set[str] = set()
    for specification in specifications:
        filename = specification["source"]
        source_path = Path(filename)
        if source_path.name != filename or source_path.suffix != ".cpp":
            raise ValueError(f"Source must be a single .cpp filename: {filename}")
        if filename in sources:
            raise ValueError(f"Duplicate source specification: {filename}")
        sources.add(filename)
        step_id = int(specification["step_id"])
        if step_id not in steps:
            raise ValueError(f"Example refers to an absent step: {step_id}")
        expected[step_id].append((HERE / "examples" / filename).read_text(encoding="utf-8"))
        cases = specification["cases"]
        if not cases:
            raise ValueError(f"No executable cases for {filename}")
        names: set[str] = set()
        for case in cases:
            if set(case) != {"name", "stdin", "stdout", "stderr", "returncode"}:
                raise ValueError(f"Incomplete case schema: {filename}, {case.get('name')}")
            if case["name"] in names:
                raise ValueError(f"Duplicate case name: {filename}, {case['name']}")
            names.add(case["name"])
            if not all(isinstance(case[key], str) for key in ("name", "stdin", "stdout", "stderr")):
                raise ValueError(f"Expected string fields in case: {filename}")
            if type(case["returncode"]) is not int:
                raise ValueError(f"Expected integer returncode: {filename}")
    if sources != {path.name for path in (HERE / "examples").glob("*.cpp")}:
        raise ValueError("Every .cpp file must have exactly one case specification")

    checks = []
    for step_id, (path, step) in steps.items():
        parser = CppBlocks()
        parser.feed(step["block"]["text"])
        parser.close()
        if parser.current is not None:
            raise ValueError(f"Unclosed C++ block: {step_id}")
        if not expected[step_id] or Counter(parser.blocks) != Counter(expected[step_id]):
            raise ValueError(f"C++ files and HTML blocks differ: {step_id}")
        checks.append({"step_id": step_id, "source": path.relative_to(HERE).as_posix(),
                       "cpp_blocks": len(parser.blocks), "only_block_text_changed": True,
                       "status": "passed"})
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default="g++")
    parser.add_argument("--report", type=Path, default=Path("validation.json"),
                        help="absolute path or a path relative to this package")
    parser.add_argument("--std", action="append", choices=("c++17", "c++20"),
                        help="repeat for selected standards; default: both")
    args = parser.parse_args()
    report_path = args.report if args.report.is_absolute() else HERE / args.report
    standards = args.std or ["c++17", "c++20"]
    report = {"schema_version": 1, "status": "running", "all_passed": False,
              "started_at": now(), "compiler_command": args.compiler, "standards": standards,
              "flags": FLAGS, "input_sha256": {}, "material_checks": [], "results": [],
              "counts": {"steps": 0, "programs": 0, "compilations": 0, "runtime_cases": 0}}
    # Invalidate a previous success before reading inputs or starting the compiler.
    save_report(report_path, report)
    try:
        report["input_sha256"] = inputs()
        specifications = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["examples"]
        report["material_checks"] = check_materials(specifications)
        report["counts"]["steps"] = len(report["material_checks"])
        report["counts"]["programs"] = len(specifications)
        version = subprocess.run([args.compiler, "--version"], text=True, capture_output=True,
                                 check=True, timeout=15)
        report["compiler"] = version.stdout.splitlines()[0]
        save_report(report_path, report)
        with tempfile.TemporaryDirectory(prefix="stepik-functions-") as folder:
            for standard in standards:
                for specification in specifications:
                    source = HERE / "examples" / specification["source"]
                    binary = Path(folder) / (source.stem + "-" + standard)
                    result = {"source": specification["source"], "step_id": specification["step_id"],
                              "standard": standard, "status": "running", "cases": []}
                    report["results"].append(result)
                    command = [args.compiler, f"-std={standard}", *FLAGS, str(source), "-o", str(binary)]
                    completed = subprocess.run(command, text=True, capture_output=True, timeout=30)
                    if completed.returncode != 0:
                        result.update({"status": "failed", "phase": "compilation",
                                       "compiler_stdout": completed.stdout, "compiler_stderr": completed.stderr})
                        raise RuntimeError(f"Compilation failed: {source.name}, {standard}")
                    report["counts"]["compilations"] += 1
                    for case in specification["cases"]:
                        execution = subprocess.run([str(binary)], input=case["stdin"], text=True,
                                                   capture_output=True, timeout=5)
                        actual = {"returncode": execution.returncode,
                                  "stdout": execution.stdout, "stderr": execution.stderr}
                        expected = {key: case[key] for key in ("returncode", "stdout", "stderr")}
                        case_result = {"name": case["name"], "status": "passed"}
                        result["cases"].append(case_result)
                        if actual != expected:
                            case_result.update({"status": "failed", "expected": expected, "actual": actual})
                            result["status"] = "failed"
                            raise RuntimeError(f"Unexpected result: {source.name}, {standard}, {case['name']}")
                        report["counts"]["runtime_cases"] += 1
                    result["status"] = "passed"
                    save_report(report_path, report)
        if inputs() != report["input_sha256"]:
            raise RuntimeError("Validation inputs changed during verification")
        report.update({"status": "passed", "all_passed": True, "finished_at": now()})
        save_report(report_path, report)
        print(json.dumps({"status": report["status"], "counts": report["counts"]}, ensure_ascii=False))
        return 0
    except BaseException as error:
        for result in report["results"]:
            if result["status"] == "running":
                result["status"] = "failed"
        report.update({"status": "failed", "all_passed": False, "finished_at": now(),
                       "error": f"{type(error).__name__}: {error}"})
        save_report(report_path, report)
        print(json.dumps({"status": "failed", "error": report["error"]}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
