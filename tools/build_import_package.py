#!/usr/bin/env python3
"""Build a reviewed Stepik .step import package from the edited step files.

Run from the repository root:
    python3 tools/build_import_package.py

The original course.json/raw export is the comparison baseline. Only blocks
that differ from that baseline enter the ZIP. This tool makes no network calls.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import html
import json
import re
import zipfile
from pathlib import Path

from review_renderer import readable_html


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def changed_fields(old, new, prefix="block"):
    if old == new:
        return []
    if isinstance(old, dict) and isinstance(new, dict):
        result = []
        for key in sorted(set(old) | set(new)):
            path = f"{prefix}.{key}"
            result.extend(changed_fields(old.get(key), new.get(key), path))
        return result
    return [prefix]


def inspect_steps(root, course_id):
    source_root = root / "courses" / str(course_id)
    bundle = json.loads((source_root / "course.json").read_text(encoding="utf-8"))
    sources = {int(s["id"]): s for s in bundle["step_sources"]}
    lessons = {int(s["id"]): s for s in bundle["lessons"]}
    sections = {int(s["id"]): s for s in bundle["sections"]}
    units = {int(s["lesson"]): s for s in bundle["units"]}
    seen, changed, checks = set(), [], collections.Counter()
    for path in sorted((source_root / "steps").glob("*/*.step")):
        content = path.read_bytes()
        item = json.loads(content)
        sid = int(item["id"])
        if sid in seen or sid not in sources:
            raise ValueError(f"Unexpected or duplicate step: {sid}")
        seen.add(sid)
        source = sources[sid]
        block, original = item["block"], source["block"]
        expected_name = f"{source['position']:02d}_{sid}_{original['name']}.step"
        if path.name != expected_name or path.parent.name != str(source["lesson"]):
            raise ValueError(f"Path does not match the original placement: {path}")
        if block["name"] != original["name"]:
            raise ValueError(f"Step type changed: {sid}")
        if not isinstance(block.get("text"), str) or not isinstance(item.get("time"), str):
            raise ValueError(f"Incomplete .step envelope: {sid}")
        checks["step_files_valid"] += 1
        if canonical(block) == canonical(original):
            continue
        author = block.get("source") or {}
        if block["name"] == "choice":
            options = author.get("options", [])
            correct = sum(o.get("is_correct") is True for o in options)
            multiple = author.get("is_multiple_choice", False)
            if not options or correct < 1 or (not multiple and correct != 1):
                raise ValueError(f"Invalid answer cardinality: {sid}")
            sample_size = author.get("sample_size")
            if isinstance(sample_size, int) and sample_size > len(options):
                raise ValueError(f"sample_size exceeds option count: {sid}")
            if block.get("options", {}).get("is_multiple_choice", multiple) != multiple:
                raise ValueError(f"Conflicting choice modes: {sid}")
            checks["changed_choice_keys_structurally_valid"] += 1
        if block["name"] == "code":
            code = author.get("code", "")
            if code:
                ast.parse(code, filename=f"step-{sid}-checker.py")
                checks["changed_checker_syntax_valid"] += 1
            sample_count = author.get("samples_count", 0)
            if block.get("options", {}).get("samples") != author.get("test_cases", [])[:sample_count]:
                raise ValueError(f"Public samples differ from author test cases: {sid}")
            checks["changed_code_samples_synchronized"] += 1
        unit = units[int(source["lesson"])]
        section = sections[int(unit["section"])]
        archive_path = (
            f"{section['position']:02d}/"
            f"{unit['position']:02d}_lesson_{source['lesson']}/{path.name}"
        )
        changed.append({
            "step_id": sid, "lesson_id": source["lesson"],
            "module": section["position"], "module_title": section["title"],
            "lesson_number": unit["position"], "lesson_title": lessons[int(source["lesson"])]["title"],
            "position": source["position"], "type": block["name"],
            "repository_path": str(path.relative_to(root)), "archive_path": archive_path,
            "step_url": f"https://stepik.org/lesson/{source['lesson']}/step/{source['position']}",
            "file_sha256": digest(content), "original_block_sha256": digest(canonical(original)),
            "revised_block_sha256": digest(canonical(block)),
            "changed_fields": changed_fields(original, block),
        })
    if seen != set(sources):
        raise ValueError(f"Missing .step files: {sorted(set(sources) - seen)}")
    changed.sort(key=lambda s: (s["module"], s["lesson_number"], s["position"]))
    return bundle, changed, dict(checks)


def build(root, course_id, date):
    out = root / "imports" / str(course_id)
    ledger_path = out / "changes.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    audit = json.loads((root / "audit/findings.json").read_text(encoding="utf-8"))
    findings = {f["id"]: f for f in audit["findings"]}
    entries = ledger["findings"]
    if len(entries) != len(findings) or {e["finding_id"] for e in entries} != set(findings):
        raise ValueError("The change ledger must account for every audit finding exactly once")
    bundle, changed, checks = inspect_steps(root, course_id)
    changed_ids = {s["step_id"] for s in changed}
    by_step = collections.defaultdict(list)
    for entry in entries:
        if entry["status"] not in {"fixed", "partial", "not_applicable"}:
            raise ValueError(f"Unknown finding status: {entry['finding_id']}")
        if entry["status"] == "fixed" and not entry["changed_step_ids"]:
            raise ValueError(f"Fixed finding has no revised step: {entry['finding_id']}")
        for sid in entry["changed_step_ids"]:
            if sid not in changed_ids:
                raise ValueError(f"Ledger names an unchanged step {sid}: {entry['finding_id']}")
            by_step[sid].append(entry["finding_id"])
    for step in changed:
        step["finding_ids"] = sorted(set(by_step[step["step_id"]]))
    archive_name = f"stepik-{course_id}-corrections-{date}.zip"
    status_counts = dict(collections.Counter(e["status"] for e in entries))
    manifest = {
        "schema_version": 1, "course_id": course_id, "date": date,
        "format": "Stepik .step: block, id, time", "deployment_status": "pending_user_import",
        "baseline_content_commit": audit["source_commit"],
        "baseline_bundle_sha256": digest((root / f"courses/{course_id}/course.json").read_bytes()),
        "archive": archive_name, "changed_steps": len(changed),
        "changed_lessons": len({s["lesson_id"] for s in changed}),
        "finding_status_counts": status_counts, "structural_checks": checks, "steps": changed,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(dump(manifest), encoding="utf-8")
    readme = [f"# Исправленные шаги курса {course_id}", "",
        f"Подготовлено **{date}**: **{len(changed)} изменённых шагов** в **{manifest['changed_lessons']} уроках**. "
        "Это содержимое для импорта; статус применения на Stepik — ожидает импорта владельцем курса.", "",
        f"[Скачать ZIP]({archive_name}) · [Все изменения](changes.md) · [Превью](preview.html) · [Манифест](manifest.json)", "",
        "## Как пользоваться", "",
        "1. Скачайте и распакуйте ZIP. Внутри находятся только изменённые `.step`, сгруппированные по номеру модуля и уроку.",
        "2. Найдите нужный урок по таблице ниже. Имя файла содержит исходную позицию, ID и тип шага.",
        "3. Импортируйте `.step` в редакторе соответствующего урока и проверьте результат перед сохранением. ZIP является упаковкой файлов: его нужно распаковать.",
        "4. Сверьте порядок и состав шагов. ID в файле нужен для сопоставления с исходником; пакет не выполняет автоматическую замену существующих шагов или перенос прогресса учащихся.",
        "5. Для изменённых заданий запустите проверку в редакторе Stepik: корректное решение должно приниматься, ошибочное — отклоняться. Локальные проверки перечислены в validation.json.", "",
        "Импорт шагов описан в [справке Stepik](https://help.stepik.org/article/54791). "
        "Оболочка файлов соответствует [официальному примеру экспорта](https://github.com/StepicOrg/Stepik-API/blob/master/examples/export_course.py).", "",
        "## Где находятся актуальные файлы", "",
        f"Редактируемые шаги — `courses/{course_id}/steps/`. `course.json`, `raw/` и исходная папка `review/` сохраняют снимок до исправлений. "
        "Превью этого пакета построено из новых `.step`. Повторную выгрузку после импорта сохраняйте в новый каталог, чтобы не затереть подготовленные правки.", "",
        "## Порядок импорта по урокам", "", "| Урок | Название | Шагов | Папка в ZIP |", "|---|---|---:|---|"]
    grouped = collections.defaultdict(list)
    for step in changed:
        grouped[(step["module"], step["lesson_number"], step["lesson_id"])].append(step)
    for (module, number, lid), group in grouped.items():
        title = group[0]["lesson_title"].replace("|", "\\|")
        readme.append(f"| [{module}.{number}](https://stepik.org/lesson/{lid}) | {title} | {len(group)} | `{module:02d}/{number:02d}_lesson_{lid}/` |")
    (out / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    changes = ["# Внесённые исправления", "", "Все статусы относятся к файлам репозитория. Импорт на Stepik выполняет владелец курса.", "",
        "[Пакет импорта](README.md) · [Машиночитаемый журнал](changes.json)", ""]
    labels = {"fixed": "Исправлено в .step", "partial": "Исправлено частично", "not_applicable": "Пересмотрено после проверки"}
    for entry in sorted(entries, key=lambda e: e["finding_id"]):
        f = findings[entry["finding_id"]]
        changes += [f"<a id=\"{f['id'].lower()}\"></a>", "", f"## {f['id']} · {f['title']}", "",
            f"**{labels[entry['status']]}.** {entry['summary']}", "",
            "**Проверка:** " + entry["validation"], ""]
        if entry.get("decision"):
            changes += ["**Принятое уточнение:** " + entry["decision"], ""]
        links = []
        for sid in entry["changed_step_ids"]:
            step = next(s for s in changed if s["step_id"] == sid)
            links.append(f"[{sid}](../../{step['repository_path']})")
        changes += ["**Файлы шагов:** " + ", ".join(links) + ".", ""]
    if ledger.get("additional_changes"):
        changes += ["## Дополнительные исправления", ""]
        for entry in ledger["additional_changes"]:
            changes += [f"**Шаг {entry['step_id']}.** {entry['summary']}", "",
                entry.get("decision", ""), "", "**Проверка:** " + entry["validation"], ""]
    (out / "changes.md").write_text("\n".join(changes) + "\n", encoding="utf-8")
    preview = ["<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\">",
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src https:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
        "<title>Исправленные шаги — превью для автора</title><style>body{max-width:1000px;margin:2em auto;padding:0 1em;font:17px/1.6 system-ui;color:#17202a}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:1em}img{max-width:100%;height:auto}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:.4em}section{border-top:2px solid #c8d4df;margin-top:2em;padding-top:1em}.answer{padding:.35em}.correct{border-left:4px solid #32814c}.wrong{border-left:4px solid #a14545}summary{cursor:pointer}</style></head><body>",
        "<h1>Исправленные шаги</h1><p>Превью для автора: варианты помечены правильными и неправильными. Это служебное представление, а не текст для учащихся.</p>"]
    for step in changed:
        block = json.loads((root / step["repository_path"]).read_text(encoding="utf-8"))["block"]
        title = f"{step['module']}.{step['lesson_number']}, шаг {step['position']} — {step['lesson_title']}"
        preview += [f'<section id="step-{step["step_id"]}"><h2>{html.escape(title)}</h2>',
            f'<p>ID {step["step_id"]} · {html.escape(step["type"])} · <a href="../../{step["repository_path"]}">Файл .step</a></p>',
            readable_html(block["text"])]
        author = block.get("source") or {}
        if block["name"] == "choice":
            for option in author.get("options", []):
                correct = option.get("is_correct", False)
                preview.append(f'<div class="answer {"correct" if correct else "wrong"}"><b>{"Верно" if correct else "Неверно"}:</b> ' +
                    (readable_html(option["text"]) if author.get("is_html_enabled") else html.escape(option["text"])) + "</div>")
        elif block["name"] != "text":
            selected = {k:v for k,v in author.items() if k not in {"test_cases", "code_templates", "code_templates_header", "code_templates_footer"}}
            if "test_cases" in author:
                selected["saved_test_case_count"] = len(author["test_cases"])
            preview.append("<details><summary>Авторские настройки и проверка</summary><pre>" + html.escape(dump(selected)) + "</pre></details>")
        preview.append("</section>")
    preview.append("</body></html>\n")
    (out / "preview.html").write_text("\n".join(preview), encoding="utf-8")
    zip_date = tuple(map(int, date.split("-"))) + (0, 0, 0)
    archive = out / archive_name
    packaged_readme = (out / "README.md").read_text(encoding="utf-8").replace(
        f"[Скачать ZIP]({archive_name})",
        "[Версия в репозитории](https://github.com/Vadimohka/stepik-OAiP/tree/main/imports/86957)")
    packaged_changes = (out / "changes.md").read_text(encoding="utf-8")
    packaged_preview = (out / "preview.html").read_text(encoding="utf-8")
    for step in changed:
        packaged_changes = packaged_changes.replace("../../" + step["repository_path"], step["archive_path"])
        packaged_preview = packaged_preview.replace("../../" + step["repository_path"], step["archive_path"])
    archive_entries = [("README.md", packaged_readme.encode()),
        ("manifest.json", (out / "manifest.json").read_bytes()),
        ("changes.json", ledger_path.read_bytes()),
        ("changes.md", packaged_changes.encode()), ("preview.html", packaged_preview.encode())]
    if (out / "validation.json").exists():
        archive_entries.append(("validation.json", (out / "validation.json").read_bytes()))
    for evidence in sorted((out / "validation").rglob("*")):
        if evidence.is_file() and evidence.suffix in {".py", ".cpp", ".c", ".json", ".md"}:
            archive_entries.append((str(evidence.relative_to(out)), evidence.read_bytes()))
    archive_entries += [(s["archive_path"], (root / s["repository_path"]).read_bytes()) for s in changed]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path, data in archive_entries:
            info = zipfile.ZipInfo(path, date_time=zip_date)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        for step in changed:
            if digest(z.read(step["archive_path"])) != step["file_sha256"]:
                raise ValueError(f"ZIP file differs from source: {step['step_id']}")
    return {"changed_steps": len(changed), "changed_lessons": manifest["changed_lessons"],
        "finding_status_counts": status_counts, "structural_checks": checks,
        "archive": str(archive.relative_to(root)), "archive_bytes": archive.stat().st_size,
        "archive_sha256": digest(archive.read_bytes()), "archive_files_verified": len(changed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", type=int, default=86957)
    parser.add_argument("--date", default="2026-11-22")
    parser.add_argument("--inspect-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.inspect_only:
        _, changed, checks = inspect_steps(root, args.course)
        result = {"changed_steps": len(changed), "structural_checks": checks}
    else:
        result = build(root, args.course, args.date)
        if (root / 'imports' / str(args.course) / 'round2_changes.json').exists():
            from build_round2_package import augment
            result['round2'] = augment(root, args.course, result['archive'])
            archive = root / result['archive']
            result['archive_bytes'] = archive.stat().st_size
            result['archive_sha256'] = digest(archive.read_bytes())
    print(dump(result), end="")


if __name__ == "__main__":
    main()
