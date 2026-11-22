#!/usr/bin/env python3
"""Reproduce the confirmed foundation defects against current staged .step files.

Run from any directory. Requires Python 3, GCC and G++. Temporary source files
and binaries are removed automatically. This never publishes to Stepik.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = "d936c0ee8d9f720ba26fec1b109a1153ae3b5930"
IDS = {3177504, 3215105, 3177565, 3177651, 3213207, 3213210,
       4700496, 3438841, 3267786}


def pair(step_id):
    original = next((ROOT / "courses/86957/steps").glob(f"*/*_{step_id}_*.step"))
    staged = ROOT / "corrections/86957/steps" / original.parent.name / original.name
    return original, staged, json.loads(original.read_text()), json.loads(staged.read_text())


def blocks(step):
    return [html.unescape(re.sub(r"<[^>]*>", "", block))
            for block in re.findall(r"<pre[^>]*>(.*?)</pre>", step["block"]["text"], re.S)]


def differences(left, right, path=""):
    if left == right:
        return []
    if isinstance(left, dict) and isinstance(right, dict) and left.keys() == right.keys():
        result = []
        for key in left:
            result.extend(differences(left[key], right[key], f"{path}.{key}".lstrip(".")))
        return result
    return [path]


def compile_code(code, standard, label, temporary):
    is_c = standard in {"c11", "c17"}
    compiler = "gcc" if is_c else "g++"
    source = temporary / (label + (".c" if is_c else ".cpp"))
    binary = temporary / label
    source.write_text(code)
    flags = [f"-std={standard}", "-Wall", "-Wextra", "-Wpedantic", "-pedantic-errors"]
    completed = subprocess.run([compiler, *flags, str(source), "-o", str(binary)],
                               capture_output=True, text=True, timeout=30)
    record = {"standard": standard, "exit_code": completed.returncode,
              "compiler_flags": flags,
              "diagnostic_excerpt": completed.stderr.replace(str(temporary), "<tmp>")[:1100]}
    return binary, record


def execute(binary, data=""):
    completed = subprocess.run([str(binary)], input=data.encode(), capture_output=True, timeout=5)
    return {"exit_code": completed.returncode,
            "stdout": completed.stdout.decode(errors="backslashreplace"),
            "stderr": completed.stderr.decode(errors="backslashreplace")}


def snippet_program(step_id, index, code):
    if step_id == 3177504:
        condition = "a == 8 && b == 2" if index == 0 else "a == 7 && b == 2 && c == 7 && d == -10"
        return "int main() {\n" + code + "\nreturn (" + condition + ") ? 0 : 1;\n}"
    if step_id == 3215105 and index == 2:
        return '#include <iostream>\nint main() { int x = 2; switch (x) {\n' + code + "\n}}"
    if step_id == 3177651 and index == 2:
        return "#include <iostream>\nint main() {\n" + code + "\n}"
    return code


def check_nbsp(temporary):
    squares = "".join(f"{i} * {i} = {i*i}\n" for i in range(1, 10))
    selected = {3177504: {0: "", 1: ""},
                3215105: {1: "x = 2\n", 2: "x = 2\n", 4: "x = 2\nx = 3\nx is undefined\n"},
                3177565: {1: squares}, 3177651: {1: squares, 2: squares}}
    results = []
    for step_id, examples in selected.items():
        _, _, before, after = pair(step_id)
        before_blocks, after_blocks = blocks(before), blocks(after)
        # Restrict the patch to U+00A0 in pre blocks, including their explanatory templates.
        expected_html = re.sub(r"<pre[^>]*>.*?</pre>",
                               lambda m: m.group(0).replace("\u00a0", " "),
                               before["block"]["text"], flags=re.S)
        assert after["block"]["text"] == expected_html
        for index, output in examples.items():
            for standard in ("c++17", "c++20"):
                row = {"step_id": step_id, "pre_index": index, "standard": standard}
                for version, code_blocks in (("before", before_blocks), ("after", after_blocks)):
                    code = snippet_program(step_id, index, code_blocks[index])
                    binary, compilation = compile_code(code, standard,
                                                       f"nbsp_{step_id}_{index}_{standard}_{version}", temporary)
                    if version == "before":
                        assert compilation["exit_code"] != 0, (step_id, index, standard)
                    else:
                        assert compilation["exit_code"] == 0, compilation
                        run = execute(binary)
                        assert run == {"exit_code": 0, "stdout": output, "stderr": ""}, run
                        compilation["run"] = run
                    row[version] = compilation
                results.append(row)
    return results


def word_cases():
    words = [f"word{i}" for i in range(25)]
    return [
        {"name": "empty", "input": "", "stdout": "", "exit_code": 0},
        {"name": "whitespace_only", "input": " \t\n\r\v\f", "stdout": "", "exit_code": 0},
        {"name": "immediate_end", "input": "end ignored", "stdout": "", "exit_code": 0},
        {"name": "ordinary", "input": "alpha beta end ignored", "stdout": "alpha\nbeta\n", "exit_code": 0},
        {"name": "eof_after_word", "input": "alpha beta", "stdout": "alpha\nbeta\n", "exit_code": 0},
        {"name": "all_whitespace_separators", "input": "a\tb\nc\rd\ve\ff end", "stdout": "a\nb\nc\nd\ne\nf\n", "exit_code": 0},
        {"name": "two_reallocations", "input": " ".join(words) + " end", "stdout": "\n".join(words) + "\n", "exit_code": 0},
        {"name": "126_bytes", "input": "a" * 126 + " end", "stdout": "a" * 126 + "\n", "exit_code": 0},
        {"name": "127_bytes_then_delimiter", "input": "a" * 127 + " end", "stdout": "a" * 127 + "\n", "exit_code": 0},
        {"name": "127_bytes_then_eof", "input": "a" * 127, "stdout": "a" * 127 + "\n", "exit_code": 0},
        {"name": "128_bytes", "input": "a" * 128 + " end", "stdout": "", "exit_code": 1},
        {"name": "false_end_suffix", "input": "a" * 127 + "end tail end", "stdout": "", "exit_code": 1},
        {"name": "free_prior_words_on_rejection", "input": "keep " + "a" * 128 + " end", "stdout": "keep\n", "exit_code": 1},
        {"name": "end_prefix_is_word", "input": "endless end", "stdout": "endless\n", "exit_code": 0},
        {"name": "utf8_126_bytes", "input": "я" * 63 + " end", "stdout": "я" * 63 + "\n", "exit_code": 0},
        {"name": "utf8_128_bytes", "input": "я" * 64 + " end", "stdout": "", "exit_code": 1},
    ]


def check_word_readers(temporary):
    cases = word_cases()
    (OUT / "word_reader_cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n")
    results = []
    for step_id in (3213207, 3213210):
        _, _, before, after = pair(step_id)
        for standard in ("c11", "c17"):
            row = {"step_id": step_id, "standard": standard, "cases": []}
            programs = {}
            for version, step in (("before", before), ("after", after)):
                code = next(code for code in blocks(step) if 'char buffer[128]' in code)
                binary, compilation = compile_code(code, standard, f"words_{step_id}_{standard}_{version}", temporary)
                assert compilation["exit_code"] == 0, compilation
                programs[version] = binary
                row[version + "_compilation"] = compilation
            for case in cases:
                expected = {"exit_code": case["exit_code"], "stdout": case["stdout"],
                            "stderr": "Word is too long\n" if case["exit_code"] else ""}
                after_run = execute(programs["after"], case["input"])
                assert after_run == expected, (step_id, standard, case["name"], after_run)
                before_run = execute(programs["before"], case["input"])
                if case["exit_code"] == 0:
                    assert before_run == expected, (step_id, standard, case["name"])
                else:
                    assert before_run["exit_code"] == 0 and before_run != expected
                if case["name"] == "128_bytes":
                    assert before_run["stdout"] == "a" * 127 + "\na\n"
                if case["name"] == "false_end_suffix":
                    assert before_run["stdout"] == "a" * 127 + "\n"
                row["cases"].append({"name": case["name"], "passed": True,
                                     "before": before_run, "after": after_run})
            results.append(row)
    return results


def check_output_quiz(temporary):
    _, _, before, after = pair(3267786)
    # Transcription of the existing image. The required headers are the wrapper.
    code = '''#include <iostream>
#include <iomanip>
int main() {
    std::cout << "Hello, World!" << '\\n';
    std::cout << std::setbase(16) << std::scientific << std::setprecision(4);
    std::cout << 125;
    std::cout << 36.23415;
    return 0;
}
'''
    source_before, source_after = before["block"]["source"], after["block"]["source"]
    assert source_before["case_sensitive"] is False and source_after["case_sensitive"] is True
    assert not source_after["use_re"] and not source_after["match_substring"]
    pattern = source_after["pattern"]
    results = []
    for standard in ("c++17", "c++20"):
        binary, compilation = compile_code(code, standard, f"quiz_{standard}", temporary)
        assert compilation["exit_code"] == 0, compilation
        run = execute(binary)
        assert run == {"exit_code": 0, "stdout": pattern, "stderr": ""}, run
        results.append({"standard": standard, "compilation": compilation, "run": run})
    variants = [pattern, pattern.replace("Hello", "hello"), pattern.replace("Hello", "HELLO"),
                pattern.replace("7d", "7D").replace("e+", "E+")]
    checks = []
    for reply in variants:
        # This checks the case flag's documented meaning for ASCII strings only;
        # it is not a reimplementation or live execution of Stepik's full checker.
        insensitive = reply.casefold() == pattern.casefold()
        sensitive = reply == pattern
        assert insensitive and (sensitive == (reply == variants[0]))
        checks.append({"reply": reply, "case_insensitive_equal": insensitive, "case_sensitive_equal": sensitive})
    return {"program": code, "compilations": results, "case_checks": checks,
            "scope": "Local ASCII comparison and source-flag verification; no Stepik submission and no newline-policy changes."}


def main():
    preservation = []
    for step_id in sorted(IDS):
        original, staged, before, after = pair(step_id)
        changed = differences(before, after)
        expected = ["block.source.case_sensitive"] if step_id == 3267786 else ["block.text"]
        assert changed == expected, (step_id, changed)
        base_bytes = subprocess.run(["git", "show", f"{BASE}:{original.relative_to(ROOT)}"],
                                    cwd=ROOT, capture_output=True, check=True).stdout
        assert original.read_bytes() == base_bytes, original
        preservation.append({"step_id": step_id, "changed_fields": changed,
                             "source_sha256": hashlib.sha256(base_bytes).hexdigest(),
                             "source_unchanged_from_base": True,
                             "staged_path": str(staged.relative_to(ROOT))})
    with tempfile.TemporaryDirectory(prefix="stepik-foundations-") as directory:
        temporary = Path(directory)
        report = {"base_commit": BASE,
                  "compiler": subprocess.run(["g++", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0],
                  "c_compiler": subprocess.run(["gcc", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0],
                  "preservation": preservation,
                  "nbsp_examples": check_nbsp(temporary),
                  "word_readers": check_word_readers(temporary),
                  "output_quiz": check_output_quiz(temporary),
                  "documentation_checks": [
                      {"step_id": 3438841, "source": "https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf",
                       "section": "6.2 Stacks; 6.2.5 Stack Behavior in 64-Bit Mode",
                       "verified_claim": "PUSH decreases the stack pointer before storing the newly pushed value."},
                      {"step_ids": [3213207, 3213210], "source": "https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf",
                       "section": "7.21.6.2 paragraph 9; 7.21.6.4; 7.4 paragraph 1",
                       "verified_claim": "A scanf field width leaves a token suffix unread; isspace is called only with EOF or an unsigned-char value."}],
                  "limitations": ["GCC only; this does not claim portability testing on every compiler.",
                                  "malloc/realloc allocation-failure injection and live Stepik grading were not executed.",
                                  "Product-task answers and its relative-gap promise are checked separately by check_task_references.py."]}
    (OUT / "fix_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"changed_steps": len(preservation),
                      "nbsp_before_after_pairs": len(report["nbsp_examples"]),
                      "word_reader_runs_per_version": sum(len(row["cases"]) for row in report["word_readers"]),
                      "quiz_compilations": len(report["output_quiz"]["compilations"]),
                      "status": "passed"}))


if __name__ == "__main__":
    main()
