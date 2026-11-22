#!/usr/bin/env python3
"""Syntax-check the 75 complete programs identified during the manual review.

Read current staged corrections when present; otherwise use the source snapshot.
This is a syntax check, not an execution or a proof that arbitrary fragments are
correct. Two teaching examples intentionally fail compilation.
"""
from pathlib import Path
import html
import json
import re
import subprocess


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EXPECTED_ERRORS = {
    (3201189, 0): "The namespace lesson intentionally uses unqualified cout.",
    (3428581, 0): "The question intentionally tries to change a const pointer.",
}


def main():
    coverage = json.loads((ROOT / "corrections/86957/foundations_coverage.json").read_text())
    results = []
    for step in coverage["steps"]:
        if not step["full_example_compilation"]:
            continue
        original = ROOT / step["path"]
        staged = ROOT / "corrections/86957/steps" / original.parent.name / original.name
        selected = staged if staged.exists() else original
        data = json.loads(selected.read_text())
        snippets = [html.unescape(re.sub(r"<[^>]*>", "", block))
                    for block in re.findall(r"<pre[^>]*>(.*?)</pre>", data["block"]["text"], re.S)]
        for test in step["full_example_compilation"]:
            index, standard = test["pre_index"], test["standard"]
            code = snippets[index]
            assert "#include" in code and "int main" in code
            is_c = standard in {"c11", "c17"}
            command = ["gcc" if is_c else "g++", "-x", "c" if is_c else "c++", f"-std={standard}",
                       "-Wall", "-Wextra", "-Wpedantic", "-pedantic-errors", "-fsyntax-only", "-"]
            compiled = subprocess.run(command, input=code, text=True, capture_output=True, timeout=30)
            expected_error = EXPECTED_ERRORS.get((step["step_id"], index))
            passed = (compiled.returncode != 0) if expected_error else (compiled.returncode == 0)
            results.append({"step_id": step["step_id"], "path": str(selected.relative_to(ROOT)),
                            "pre_index": index, "standard": standard, "exit_code": compiled.returncode,
                            "expected_error": expected_error, "passed": passed,
                            "diagnostic_excerpt": compiled.stderr[:900]})
    report = {"scope": "Syntax only; staged corrections take precedence; C examples use C11/C17.",
              "compiler": subprocess.run(["g++", "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0],
              "complete_programs": len({(r["step_id"], r["pre_index"]) for r in results}),
              "compilations": len(results), "successes": sum(r["exit_code"] == 0 for r in results),
              "intentional_errors": sum(bool(r["expected_error"]) for r in results),
              "unexpected_results": sum(not r["passed"] for r in results), "results": results}
    (OUT / "full_examples_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}))
    assert report["complete_programs"] == 75 and report["compilations"] == 150
    assert report["unexpected_results"] == 0


if __name__ == "__main__":
    main()
