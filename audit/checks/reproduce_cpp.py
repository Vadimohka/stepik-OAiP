#!/usr/bin/env python3
"""Selected compiler evidence for the first proofreading pass.

Runs only the small, reviewed examples shipped in cpp/, never source extracted
at runtime from the course. Temporary executables and data stay in a temporary
directory. ABI-specific results are observations, not portable guarantees.
"""
import argparse
import json
import platform
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = [
    ("checks", "c++20", True, "", "all_safe_checks_passed"),
    ("avl", "c++20", True, "", "3:two"),
    ("avl_fixed", "c++20", True, "", "3:three"),
    ("hash", "c++20", True, "", "1:first"),
    ("hash_fixed", "c++20", True, "", "2:updated"),
    ("motion", "c++20", True, "0.12415 0.51251351 0.51515251525\n",
     "0.28032787010526721269 | 0.28032787010526721272"),
    ("long_float", "c++20", False, "", None),
    ("wchar", "c++17", True, "", "119"),
    ("wchar", "c++20", False, "", None),
    ("array_partial", "c++11", True, "", "4 3 0"),
    ("new_char_braces20", "c++20", True, "", "Hello"),
    ("sum_digits", "c++17", True, "", "0 0 0"),
    ("static_cast_reference", "c++20", False, "", None),
    ("reinterpret_numeric", "c++20", False, "", None),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default="g++")
    args = parser.parse_args()
    version = subprocess.run([args.compiler, "--version"], text=True,
                             capture_output=True, check=True, timeout=10).stdout.splitlines()[0]
    results = []
    with tempfile.TemporaryDirectory(prefix="stepik-proofreading-", dir=HERE) as directory:
        temp = Path(directory)
        for name, standard, should_compile, stdin, expected in CASES:
            source = HERE / "cpp" / f"{name}.cpp"
            binary = temp / f"{name}-{standard}"
            command = [args.compiler, f"-std={standard}", "-Wall", "-Wextra", "-pedantic-errors",
                       str(source), "-o", str(binary)]
            compile_result = subprocess.run(command, text=True, capture_output=True, timeout=30)
            row = {"name": name, "standard": standard, "source": f"cpp/{source.name}",
                   "expected_to_compile": should_compile, "compile_returncode": compile_result.returncode,
                   "diagnostic": compile_result.stderr.replace(str(HERE), "audit/checks")[:1500]}
            row["matches_expected_compile_status"] = (compile_result.returncode == 0) == should_compile
            if should_compile and compile_result.returncode == 0:
                run = subprocess.run([str(binary)], input=stdin, text=True, capture_output=True,
                                     cwd=temp, timeout=10)
                row.update(run_returncode=run.returncode, stdout=run.stdout, stderr=run.stderr[:1000],
                           expected_output_fragment=expected,
                           matches_reference_environment=(run.returncode == 0 and expected in run.stdout))
            results.append(row)
    report = {"compiler": version, "system": platform.system(), "architecture": platform.machine(),
              "note": "Size, address layout and last decimal digits may differ on another ABI.\n"
                      "No example that deliberately dereferences invalid pointers is executed.",
              "results": results}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(r["matches_expected_compile_status"] and r.get("matches_reference_environment", True)
                    for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
