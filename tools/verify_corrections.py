#!/usr/bin/env python3
"""Verify the existing-step correction package against its captured baseline.

Run from a complete checkout of the repository, with Python 3.10+ and g++.
No network, credentials or Stepik writes are used. This is local verification.
"""
import argparse
import ast
from collections import Counter
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys

from build_corrections_package import BASE_COMMIT, ROOT, OUT, block_digest, changed_fields, digest, package_inputs, read, write


def structural_checks(manifest):
    assert manifest["base_commit"] == BASE_COMMIT
    if not manifest["publication"]["applied"]:
        snapshot = subprocess.run(["git", "diff", "--quiet", BASE_COMMIT, "--", "courses/86957"],
                                  cwd=ROOT)
        assert snapshot.returncode == 0, "Published snapshot changed relative to BASE_COMMIT"
        untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", "courses/86957"],
                                   cwd=ROOT, capture_output=True, text=True, check=True)
        assert not untracked.stdout, "Unexpected files in the published snapshot"
    assert {str(path.relative_to(ROOT)) for path in (OUT / "steps").rglob("*.step")} == {
        step["target_path"] for step in manifest["steps"]}, "Corrected step inventory differs from manifest"
    assert {str(path.relative_to(ROOT)) for path in (OUT / "baseline").rglob("*.step")} == {
        step["baseline_path"] for step in manifest["steps"]}, "Baseline inventory differs from manifest"
    bindings = {int(row["step_id"]): row for row in
                read(ROOT / "courses/86957/manifest.json")["step_files"]["bindings"]}
    blocks = {}
    for path in sorted((ROOT / "courses/86957/steps").glob("*/*.step")):
        document = read(path)
        step_id = int(document["id"])
        assert step_id not in blocks, step_id
        assert bindings[step_id]["path"] == str(path.relative_to(ROOT / "courses/86957"))
        blocks[step_id] = document["block"]
    assert set(blocks) == set(bindings)
    changed = set()
    for step in manifest["steps"]:
        sid = step["step_id"]
        assert sid not in changed
        changed.add(sid)
        before_path, after_path = ROOT / step["baseline_path"], ROOT / step["target_path"]
        before, after = read(before_path), read(after_path)
        binding = bindings[sid]
        expected_source = ROOT / "courses/86957" / binding["path"]
        assert sid == int(before["id"]) == int(after["id"])
        assert step["lesson_id"] == binding["lesson_id"]
        assert step["position"] == binding["position"]
        assert ROOT / step["source_path"] == expected_source
        assert after_path == OUT / binding["path"]
        assert before_path == OUT / "baseline" / expected_source.parent.name / expected_source.name
        declared = sorted({field for finding in step["findings"] for field in finding["changed_fields"]})
        assert declared == step["changed_fields"], (sid, "Undocumented block field change")
        assert digest(before_path.read_bytes()) == step["before_file_sha256"]
        assert digest(after_path.read_bytes()) == step["after_file_sha256"]
        assert block_digest(before["block"]) == step["before_block_sha256"]
        assert block_digest(after["block"]) == step["after_block_sha256"]
        assert changed_fields(before, after) == step["changed_fields"]
        assert {k: v for k, v in before.items() if k != "block"} == {
            k: v for k, v in after.items() if k != "block"}
        assert before["block"]["name"] == after["block"]["name"]
        if not manifest["publication"]["applied"]:
            assert (ROOT / step["source_path"]).read_bytes() == before_path.read_bytes()
        blocks[sid] = after["block"]
    code_steps = cases_count = choice_steps = 0
    for sid, block in blocks.items():
        source = block.get("source") or {}
        if block["name"] == "code":
            code_steps += 1
            ast.parse(source["code"])
            seen = {}
            cases = source.get("test_cases", [])
            for dataset, clue in cases:
                cases_count += 1
                assert dataset not in seen or seen[dataset] == clue, (sid, "Conflicting clues")
                seen[dataset] = clue
            samples = block.get("options", {}).get("samples", [])
            assert not samples or samples == cases[:len(samples)], (sid, "Samples differ")
        elif block["name"] == "choice":
            choice_steps += 1
            assert source["is_multiple_choice"] == block["options"]["is_multiple_choice"]
            correct = sum(bool(option["is_correct"]) for option in source["options"])
            assert correct >= 1 or source.get("is_always_correct"), sid
            if not source["is_multiple_choice"] and not source.get("is_always_correct"):
                assert correct == 1, sid
    return blocks, {
        "snapshot_steps": len(blocks), "block_types": dict(Counter(b["name"] for b in blocks.values())),
        "changed_steps": len(changed), "code_steps": code_steps,
        "stored_test_cases_after": cases_count, "choice_structure_checked": choice_steps,
        "metadata_identity_hashes_samples_and_grader_syntax": "passed",
    }


def run(script):
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                            capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise RuntimeError(f"{script}\n{result.stdout}\n{result.stderr}")
    return {"script": script, "returncode": result.returncode}


def previous_regressions(blocks):
    # Reuse earlier independent solvers with this package overlaid in memory.
    # Archived results must remain byte-for-byte unchanged.
    import verify_revised_steps as first
    import verify_round2 as second
    first.BLOCKS.update(blocks)
    first.RECORDS.clear()
    first.response_checks()
    first.verify_constraints_and_references()
    first.numeric_cpp_solutions()
    first_report = {"all_passed": True, "checks": first.RECORDS,
                    "scope": "Earlier regression functions on the correction overlay"}
    write(OUT / "evidence/regression/first_pass.json", first_report)
    archived = ROOT / "imports/86957/validation/round2_code_validation.json"
    saved = archived.read_bytes()
    second.RECORDS.clear()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            second.main()
        second_report = read(archived)
        # The old main hashes published files; replace that provenance with the
        # actual in-memory blocks supplied to its checker/solver functions.
        second_report.pop("code_file_sha256", None)
        second_report["scope"] = "Earlier second-pass regressions on the correction overlay; not live Stepik"
        second_report["tested_block_sha256"] = {
            str(sid): block_digest(block) for sid, block in sorted(blocks.items())
            if block["name"] == "code"}
        write(OUT / "evidence/regression/second_pass.json", second_report)
    finally:
        archived.write_bytes(saved)
    return {"first_pass_checks": len(first.RECORDS), "second_pass_checks": len(second.RECORDS),
            "archived_report_restored": archived.read_bytes() == saved}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structural-only", action="store_true",
                        help="Check the manifest and schemas without claiming complete validation")
    args = parser.parse_args()
    manifest = read(OUT / "manifest.json")
    blocks, structure = structural_checks(manifest)
    if args.structural_only:
        print(json.dumps({"status": "partial", "structure": structure}, ensure_ascii=False))
        return
    # The list is explicit so missing evidence cannot silently reduce coverage.
    scripts = [
        "corrections/86957/evidence/foundations/verify_fixes.py",
        "corrections/86957/evidence/foundations/check_task_references.py",
        "corrections/86957/evidence/foundations/compile_full_examples.py",
        "corrections/86957/evidence/core/apply_and_verify_fixes.py",
        "corrections/86957/evidence/core/check_task_answers.py",
        "corrections/86957/evidence/core/check_remaining_tasks.py",
        "corrections/86957/evidence/core/check_cpp_snippets.py",
        "corrections/86957/evidence/advanced/validate_advanced.py",
        "corrections/86957/evidence/advanced/validate_invariants.py",
        "corrections/86957/evidence/advanced/validate_hash.py",
        "corrections/86957/evidence/final_task/verify_yaml_ini.py",
    ]
    runs = [run(script) for script in scripts]
    # Some evidence scripts reconstruct their own patches; require their exact
    # agreement with the reviewed package after running them.
    blocks, structure = structural_checks(manifest)
    regressions = previous_regressions(blocks)
    tree = subprocess.run([sys.executable, str(ROOT / "tools/render_course_tree.py"), "--check"],
                          cwd=ROOT, text=True, capture_output=True)
    assert tree.returncode == 0, tree.stderr
    inputs = package_inputs()
    report = {
        "course_id": 86957, "base_commit": manifest["base_commit"],
        "status": "passed", "all_passed": True, "live_stepik_execution": False,
        "scope": "Local structural, counterexample, compiler and grading regression verification",
        "structure": structure, "evidence_scripts": runs,
        "previous_regressions": regressions, "course_tree_check": "passed",
        "input_sha256": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in sorted(inputs)},
    }
    write(OUT / "validation.json", report)
    print(json.dumps({"all_passed": True, "structure": structure,
                      "previous_regressions": regressions}, ensure_ascii=False))


if __name__ == "__main__":
    main()
