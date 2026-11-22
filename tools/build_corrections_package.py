#!/usr/bin/env python3
"""Build a reviewable package for corrections to existing course steps.

This tool never contacts Stepik and never changes the published course snapshot.
The first captured baseline remains immutable on subsequent runs.
"""
import argparse
from collections import defaultdict
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "corrections/86957"
BASE_COMMIT = "d936c0ee8d9f720ba26fec1b109a1153ae3b5930"
DATE = "2026-11-23"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def block_digest(block):
    return digest(json.dumps(block, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8"))


def changed_fields(before, after, prefix=""):
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(before.keys() | after.keys()):
            name = f"{prefix}.{key}" if prefix else key
            if key not in before or key not in after:
                result.append(name)
            else:
                result.extend(changed_fields(before[key], after[key], name))
        return result
    return [prefix]


def text(record, *keys):
    return next((record[key] for key in keys if record.get(key)), "")


def priority(records):
    aliases = {"high": "P1", "medium": "P2", "low": "P3"}
    return min(aliases.get(r.get("severity"), r.get("severity", "P2"))
               for r in records)


def package_inputs():
    files = [path for path in OUT.rglob("*") if path.is_file()
             and path.suffix not in {".zip", ".pyc"}
             and path.name not in {"validation.json", "SHA256SUMS"}
             and "__pycache__" not in path.parts]
    files += [ROOT / "tools/build_corrections_package.py", ROOT / "tools/verify_corrections.py"]
    return sorted(files)


def build():
    findings = defaultdict(list)
    for journal in sorted(OUT.glob("*_findings.json")):
        records = read(journal)
        if isinstance(records, dict):
            records = records["findings"]
        for record in records:
            findings[int(record["step_id"])].append(record)
    bindings = {int(row["step_id"]): row for row in
                read(ROOT / "courses/86957/manifest.json")["step_files"]["bindings"]}
    steps = []
    for target in sorted((OUT / "steps").glob("*/*.step")):
        match = re.fullmatch(r"(\d+)_(\d+)_(.+)\.step", target.name)
        if not match:
            raise ValueError(f"Invalid step filename: {target}")
        position, step_id = map(int, match.groups()[:2])
        lesson_id = int(target.parent.name)
        source = ROOT / "courses/86957/steps" / str(lesson_id) / target.name
        baseline = OUT / "baseline" / str(lesson_id) / target.name
        before_bytes = baseline.read_bytes() if baseline.exists() else source.read_bytes()
        committed = subprocess.run(
            ["git", "show", f"{BASE_COMMIT}:{source.relative_to(ROOT)}"],
            cwd=ROOT, capture_output=True, check=True).stdout
        if before_bytes != committed:
            raise ValueError(f"Baseline differs from the recorded commit: {step_id}")
        after_bytes = target.read_bytes()
        before, after = json.loads(before_bytes), json.loads(after_bytes)
        fields = changed_fields(before, after)
        if not fields or any(not field.startswith("block.") for field in fields):
            raise ValueError(f"Empty change or changed step metadata: {step_id}")
        if before["block"]["name"] != after["block"]["name"] or int(after["id"]) != step_id:
            raise ValueError(f"Changed step identity/type: {step_id}")
        binding = bindings[step_id]
        if binding["lesson_id"] != lesson_id or binding["position"] != position:
            raise ValueError(f"Wrong lesson or position: {step_id}")
        records = findings.pop(step_id)
        if not records:
            raise ValueError(f"No documented error: {step_id}")
        declared = sorted({field for record in records for field in record["changed_fields"]})
        if fields != declared:
            raise ValueError(f"Actual and documented changed fields differ: {step_id}: {fields} != {declared}")
        for record in records:
            for evidence in record.get("evidence", []):
                if not (ROOT / evidence).is_file():
                    raise ValueError(f"Missing evidence: {evidence}")
        baseline.parent.mkdir(parents=True, exist_ok=True)
        if not baseline.exists():
            baseline.write_bytes(before_bytes)
        steps.append({
            "step_id": step_id, "lesson_id": lesson_id, "position": position,
            "block_type": after["block"]["name"], "priority": priority(records),
            "source_path": str(source.relative_to(ROOT)),
            "target_path": str(target.relative_to(ROOT)),
            "baseline_path": str(baseline.relative_to(ROOT)),
            "step_url": binding["step_url"], "changed_fields": fields,
            "before_file_sha256": digest(before_bytes),
            "after_file_sha256": digest(after_bytes),
            "before_block_sha256": block_digest(before["block"]),
            "after_block_sha256": block_digest(after["block"]),
            "summary": "; ".join(text(r, "title", "issue", "summary") for r in records),
            "findings": records,
        })
    if findings or not steps:
        raise ValueError(f"Findings without corrected files, or empty package: {list(findings)}")
    manifest = {
        "schema_version": 1, "course_id": 86957, "date": DATE,
        "base_commit": BASE_COMMIT, "status": "prepared",
        "changed_steps": len(steps),
        "confirmed_findings": sum(len(step["findings"]) for step in steps),
        "changed_lessons": len({step["lesson_id"] for step in steps}),
        "changed_fields": sorted({field for step in steps for field in step["changed_fields"]}),
        "publication": {"status": "not_applied", "applied": False,
                        "note": "Package prepared and checked locally; no Stepik mutation or live grading verification."},
        "steps": steps,
    }
    existing = OUT / "manifest.json"
    if existing.exists():
        old = read(existing)
        if old.get("publication", {}).get("status") == "verified_on_stepik":
            fingerprints = lambda m: {s["step_id"]: s["after_file_sha256"] for s in m["steps"]}
            if fingerprints(old) != fingerprints(manifest):
                raise ValueError("Published package is immutable: start another correction package")
            manifest["publication"] = old["publication"]
            manifest["status"] = old["status"]
    write(OUT / "manifest.json", manifest)
    published = manifest["publication"]["status"] == "verified_on_stepik"
    status = "Опубликован и сверен на Stepik." if published else "Подготовлен; на Stepik этим пакетом не опубликован."
    lines = ["# Исправления существующих шагов", "",
             f"Дата: {DATE}. Основа: `{BASE_COMMIT}`.", "",
             f"**{len(steps)} шагов в {manifest['changed_lessons']} уроках. {status}**", "",
             "P1 — неправильное поведение или оценивание; P2 — ошибка примера или объяснения. "
             "Приоритет описывает влияние на учебный материал, а не статус публикации.", "",
             "| Шаг | ID | Приоритет | Подтверждённая ошибка | Изменяемые поля |",
             "|---|---:|---|---|---|"]
    for step in steps:
        summary = step["summary"].replace("|", "\\|").replace("\n", " ")
        fields = ", ".join(f"`{field}`" for field in step["changed_fields"])
        lines.append(f"| [{step['lesson_id']} / {step['position']}]({step['step_url']}) "
                     f"| {step['step_id']} | {step['priority']} | {summary} | {fields} |")
    for step in steps:
        lines.extend(["", f"## {step['step_id']}: {step['summary']}", "",
                      f"[Текущий шаг]({step['step_url']}) · "
                      f"[Исправленный файл](steps/{step['lesson_id']}/{Path(step['target_path']).name})", ""])
        for record in step["findings"]:
            for key, label in (("before", "До исправления"), ("after", "После исправления")):
                if isinstance(record.get(key), str):
                    lines.extend([f"**{label}.** {record[key]}", ""])
            for key in ("rationale", "issue", "fix", "reproduction"):
                if record.get(key):
                    lines.extend([record[key], ""])
            evidence = record.get("evidence", [])
            if evidence:
                lines.append("Проверка: " + ", ".join(
                    f"[{Path(path).name}]({Path(path).relative_to('corrections/86957')})"
                    for path in evidence) + ".")
                lines.append("")
    (OUT / "CHANGES.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    preview = ["<!doctype html><html lang='ru'><meta charset='utf-8'>",
               "<meta name='viewport' content='width=device-width,initial-scale=1'>",
               "<title>Исправления существующих шагов ОАиП</title>",
               "<style>body{max-width:1050px;margin:2rem auto;padding:0 1rem;font:17px/1.6 system-ui;color:#20333b;background:#fafaf7}"
               "h1,h2{line-height:1.25}section{border-top:2px solid #31756b;margin-top:3rem;padding-top:1rem}"
               "pre{overflow:auto;background:#eaf0f3;padding:1rem;font:14px/1.5 monospace}"
               "a{color:#176960}table{border-collapse:collapse}td,th{padding:.5rem;border:1px solid #b7c7cc}"
               "img{max-width:100%;height:auto}.notice{background:#fff0c9;padding:1rem}summary{cursor:pointer;font-weight:600}</style>",
               "<h1>Исправления существующих шагов ОАиП</h1>",
               f"<p class='notice'>{html.escape(status)}</p>",
               "<p>Показаны исправленные тексты и изменения проверяющего кода. "
               "Полные тесты и поля блока сохранены в .step и манифесте.</p><ol>"]
    for step in steps:
        preview.append(f"<li><a href='#step-{step['step_id']}'>{step['step_id']}: "
                       f"{html.escape(step['summary'])}</a></li>")
    preview.append("</ol>")
    for step in steps:
        block = read(ROOT / step["target_path"])["block"]
        preview.extend([f"<section id='step-{step['step_id']}'><h2>{step['step_id']}: "
                        f"{html.escape(step['summary'])}</h2>",
                        f"<p><a href='{html.escape(step['step_url'], quote=True)}'>Шаг на Stepik</a></p>",
                        block["text"]])
        if "block.source.code" in step["changed_fields"]:
            preview.extend(["<details><summary>Исправленная проверяющая функция</summary><pre>",
                            html.escape(block["source"]["code"]), "</pre></details>"])
        preview.append("</section>")
    preview.append("</html>")
    (OUT / "preview.html").write_text("\n".join(line.rstrip() for line in
        "\n".join(preview).splitlines()) + "\n", encoding="utf-8")
    return manifest


def archive():
    report = read(OUT / "validation.json")
    if report.get("all_passed") is not True:
        raise ValueError("Complete successful validation is required")
    inputs = package_inputs()
    if set(report["input_sha256"]) != {str(path.relative_to(ROOT)) for path in inputs}:
        raise ValueError("Package file inventory changed after validation")
    for path, checksum in report["input_sha256"].items():
        if digest((ROOT / path).read_bytes()) != checksum:
            raise ValueError(f"Input changed after validation: {path}")
    destination = OUT / f"stepik-86957-corrections-{DATE}.zip"
    files = inputs + [OUT / "validation.json"]
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(files):
            info = zipfile.ZipInfo(str(path.relative_to(ROOT)), date_time=(2026, 11, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, path.read_bytes())
    with zipfile.ZipFile(destination) as check:
        assert check.testzip() is None
        for path in files:
            assert check.read(str(path.relative_to(ROOT))) == path.read_bytes()
    (OUT / "SHA256SUMS").write_text(f"{digest(destination.read_bytes())}  {destination.name}\n")
    print(f"Archive: {destination.relative_to(ROOT)} ({destination.stat().st_size} bytes)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", action="store_true")
    args = parser.parse_args()
    if args.archive:
        archive()
    else:
        manifest = build()
        print(json.dumps({"steps": manifest["changed_steps"], "lessons": manifest["changed_lessons"],
                          "publication": manifest["publication"]["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
