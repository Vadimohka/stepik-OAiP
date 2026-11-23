#!/usr/bin/env python3
"""Build the two 2026-11-23 course packages without contacting Stepik.

Baselines are captured once as exact bytes. Later builds verify their recorded
hashes and never refresh them from the course snapshot. --check is read-only.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = 86957
DATE = "2026-11-23"
BASE_COMMIT = "7a7db0a3061f9316cc6ae19c1b6c1d7f28888ee4"
PACKAGES = (
    ("quality-2026-11-23", "text", "Обновление объяснений и практики"),
    ("assessment-2026-11-23", "choice", "Обновление проверочных вопросов"),
)
NEW_PUBLICATION = {
    "status": "not_published",
    "applied": False,
    "note": "Подготовлено в GitHub; в Stepik в этой итерации не применялось.",
}
HASH_FIELDS = ("before_file_sha256", "after_file_sha256", "before_block_sha256", "after_block_sha256")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def block_digest(block: dict) -> str:
    return digest(json.dumps(block, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def changed_fields(before: object, after: object, prefix: str = "") -> list[str]:
    if type(before) is not type(after):
        return [prefix]
    if isinstance(before, dict):
        result = []
        for key in sorted(before.keys() | after.keys()):
            path = f"{prefix}.{key}" if prefix else key
            if key not in before or key not in after:
                result.append(path)
            else:
                result.extend(changed_fields(before[key], after[key], path))
        return result
    if isinstance(before, list):
        if len(before) != len(after):
            return [prefix]
        return [field for index, (old, new) in enumerate(zip(before, after))
                for field in changed_fields(old, new, f"{prefix}[{index}]")]
    return [] if before == after else [prefix]


def allowed_fields(before: dict, after: dict, kind: str, sid: int) -> list[str]:
    fields = changed_fields(before, after)
    require(bool(fields), f"Unchanged staged step: {sid}")
    if kind == "text":
        require(fields == ["block.text"], f"Change outside block.text: {sid}: {fields}")
    else:
        pattern = re.compile(r"block\.(?:text|feedback_correct|feedback_wrong|source\.is_options_feedback|source\.options\[\d+\]\.(?:text|is_correct|feedback))")
        require(all(pattern.fullmatch(field) for field in fields),
                f"Change outside allowed assessment fields: {sid}: {fields}")
        old_options = before["block"]["source"]["options"]
        new_options = after["block"]["source"]["options"]
        require(len(old_options) == len(new_options), f"Changed option count: {sid}")
        require(all(type(option.get("is_correct")) is bool for option in new_options),
                f"Non-boolean assessment key: {sid}")
    return fields


def load_bindings(root: Path) -> tuple[dict[int, dict], dict[int, int]]:
    course = json.loads((root / f"courses/{COURSE_ID}/manifest.json").read_bytes())
    require(course["course_id"] == COURSE_ID, "Wrong course manifest")
    bindings, order = {}, {}
    for index, binding in enumerate(course["step_files"]["bindings"]):
        sid = int(binding["step_id"])
        require(sid not in bindings, f"Duplicate course binding: {sid}")
        require(binding["course_id"] == COURSE_ID, f"Wrong bound course: {sid}")
        bindings[sid], order[sid] = binding, index
    return bindings, order


def load_changes(package: Path) -> dict[int, dict]:
    result = {}
    journals = sorted(package.glob("changes_*.json"))
    require(bool(journals), f"No changes_*.json in {package}")
    for path in journals:
        document = json.loads(path.read_bytes())
        for change in document["changes"]:
            sid = int(change["step_id"])
            require(sid not in result, f"Duplicate change record: {sid}")
            require(isinstance(change.get("summary"), str) and bool(change["summary"].strip()),
                    f"Missing summary: {sid}")
            require(isinstance(change.get("sources"), list) and bool(change["sources"])
                    and all(isinstance(url, str) and url.startswith("https://") for url in change["sources"]),
                    f"Missing or invalid source URLs: {sid}")
            result[sid] = change
    return result


class PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, value: str) -> None:
        self.parts.append(value)


def text_only(value: str) -> str:
    parser = PlainText()
    parser.feed(value)
    return " ".join("".join(parser.parts).split())


def publication_note(manifest: dict) -> str:
    publication = manifest["publication"]
    if publication.get("status") == "verified_on_stepik":
        return "Пакет опубликован и проверен через Stepik API; область проверки и дата указаны в манифесте."
    if publication.get("applied"):
        return "Сохранены имеющиеся сведения о применении пакета. Статус публикации указан в манифесте; эта сборка не проверяет платформу."
    return "Готовый пакет изменений. Ещё не опубликован на Stepik; здесь показана подготовленная редакция."


def render_changes(manifest: dict, title: str) -> bytes:
    lines = [f"# {title}", "", f"Дата подготовки: {DATE}. Базовый коммит: `{BASE_COMMIT}`.", "",
             publication_note(manifest), "", f"Изменено шагов: **{manifest['changed_steps']}**; уроков: **{manifest['changed_lessons']}**.", "",
             "Идентификаторы и размещение шагов сохранены. Исходные байты находятся в `baseline/`; новые варианты — в `steps/`.", "",
             "[Превью всех изменений](preview.html) · [Манифест и контрольные суммы](manifest.json)", "",
             "| Шаг | Урок / позиция | Изменение |", "| --- | --- | --- |"]
    for step in manifest["steps"]:
        summary = step["summary"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| [{step['step_id']}]({step['step_url']}) | {step['lesson_id']} / {step['position']} | {summary} |")
    lines.extend(["", "## Проверка и область изменений", "",
                  "`python3 tools/build_quality_packages.py --check` проверяет актуальность этого журнала, манифеста и превью без перезаписи.", "",
                  "Builder проверяет соответствие журнала набору `.step`, привязку каждого шага к снимку курса, неизменность baseline и допустимый набор изменённых полей. Он не компилирует примеры и не проверяет оценивание Stepik; для этого предусмотрены отдельные проверки.", "",
                  "Точный список изменённых полей и первичные справочные ссылки записаны отдельно для каждого шага в манифесте.", ""])
    return "\n".join(lines).encode("utf-8")


CSS = """
:root{color-scheme:light;--ink:#182e3c;--accent:#135f69;--line:#cbd7de}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f5f7f8;color:var(--ink);font:17px/1.65 system-ui,sans-serif}
header{padding:2rem max(1rem,calc((100vw - 1420px)/2));background:#143646;color:white}header a{color:#d9f3f5}h1,h2,h3,h4{line-height:1.25}
.layout{max-width:1420px;margin:auto;display:grid;grid-template-columns:300px minmax(0,1fr);gap:2rem;padding:1.5rem}
nav{position:sticky;top:1rem;align-self:start;max-height:90vh;overflow:auto;font-size:.9rem}nav ol{padding-left:1.4rem}nav li{margin:.65rem 0}
a{color:var(--accent);text-underline-offset:.15em}article{background:white;padding:1.5rem 2rem;margin-bottom:2rem;border:1px solid var(--line);border-radius:12px;scroll-margin-top:1rem}
.notice{border-left:5px solid #e3ae39;background:#fff0c9;padding:.8rem 1rem;color:#473b1b}.meta{font-size:.9rem;color:#47616f}.article-heading{border-bottom:1px solid var(--line);padding-bottom:1rem;margin-bottom:1.5rem}
pre{overflow:auto;background:#edf2f5;padding:1rem;border-radius:8px;font-size:14px;line-height:1.5}code{font-size:.91em}table{border-collapse:collapse;width:100%;display:block;overflow:auto}
th,td{border:1px solid var(--line);padding:.6rem;text-align:left;vertical-align:top}th{background:#edf2f5}details{margin:1rem 0;border:1px solid var(--line);border-radius:7px;padding:.8rem 1rem}summary{cursor:pointer;font-weight:650}.choices li{padding:.4rem 0}.teacher{background:#eef6f3}.teacher li{margin:1rem 0}.feedback{margin:.3rem 0}.sources{font-size:.9rem;border-top:1px solid var(--line);padding-top:1rem;overflow-wrap:anywhere}img{max-width:100%;height:auto}
@media(max-width:900px){.layout{display:block;padding:1rem}nav{position:static;max-height:none}article{padding:1rem}header{padding:1.5rem 1rem}}
@media print{nav{display:none}.layout{display:block}article{border:0;break-before:page}header{color:var(--ink);background:white}pre{white-space:pre-wrap}}
"""


def render_preview(root: Path, manifest: dict, title: str, documents: dict[int, dict]) -> bytes:
    esc = html.escape
    parts = ["<!doctype html>", '<html lang="ru"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             f"<title>{esc(title)} — курс {COURSE_ID}</title><style>{CSS}</style></head><body>",
             f'<header id="top"><h1>{esc(title)}</h1><p>Курс {COURSE_ID} · подготовлено {DATE} · {manifest["changed_steps"]} шагов в {manifest["changed_lessons"]} уроках</p>',
             f'<p class="notice">{esc(publication_note(manifest))}</p>',
             '<p><a href="manifest.json">Манифест</a> · <a href="CHANGES.md">Журнал изменений</a></p></header>',
             '<div class="layout"><nav aria-label="Шаги пакета"><h2>Навигация</h2><ol>']
    for step in manifest["steps"]:
        sid = step["step_id"]
        body = documents[sid]["block"]["text"]
        heading = re.search(r"<h[1-6](?:\s[^>]*)?>(.*?)</h[1-6]>", body, re.S | re.I)
        label = text_only(heading.group(1)) if heading else step["summary"]
        parts.append(f'<li><a href="#step-{sid}">{esc(label)}</a><br><span class="meta">ID {sid} · {step["lesson_id"]}/{step["position"]}</span></li>')
    parts.append("</ol></nav><main>")
    for step in manifest["steps"]:
        sid = step["step_id"]
        block = documents[sid]["block"]
        target = "/".join(PurePosixPath(step["target_path"]).parts[-3:])
        baseline = "/".join(PurePosixPath(step["baseline_path"]).parts[-3:])
        parts.extend([f'<article id="step-{sid}"><div class="article-heading"><p class="meta">ID {sid} · урок {step["lesson_id"]} · позиция {step["position"]}</p>',
                      f'<p>{esc(step["summary"])}</p><p><a href="{esc(step["step_url"], quote=True)}">Существующий шаг на Stepik</a> · <a href="{esc(target, quote=True)}">Новый .step</a> · <a href="{esc(baseline, quote=True)}">Исходный .step</a></p></div>',
                      block["text"]])
        if block["name"] == "choice":
            options = block["source"]["options"]
            parts.append('<p class="meta">Ниже авторский порядок вариантов. Настройка перемешивания на Stepik сохранена.</p><ol class="choices">')
            parts.extend(f"<li>{option['text']}</li>" for option in options)
            key = ", ".join(str(i) for i, option in enumerate(options, 1) if option["is_correct"])
            parts.extend(["</ol>", '<details class="teacher"><summary>Для преподавателя: ключ и обратная связь</summary>',
                          f'<p><strong>Верные варианты: {key}.</strong> Это ключ авторского блока; фактическое оценивание платформы здесь не воспроизводится.</p><ol>'])
            for option in options:
                verdict = "Верно" if option["is_correct"] else "Неверно"
                parts.append(f'<li><strong>{verdict}.</strong> {option["text"]}<div class="feedback">{option["feedback"]}</div></li>')
            parts.append("</ol>")
            for name, label in (("feedback_correct", "Обратная связь при верном ответе"), ("feedback_wrong", "Обратная связь при ошибке")):
                if block.get(name):
                    parts.append(f"<p><strong>{label}:</strong> {block[name]}</p>")
            parts.append("</details>")
        parts.append('<div class="sources"><strong>Справочные источники</strong><ul>')
        parts.extend(f'<li><a href="{esc(url, quote=True)}">{esc(url)}</a></li>' for url in step["sources"])
        parts.append('</ul><p><a href="#top">К началу пакета</a></p></div></article>')
    parts.append("</main></div></body></html>\n")
    return "\n".join(parts).encode("utf-8")


@dataclass
class BuildPlan:
    manifest: dict
    new_baselines: dict[Path, bytes]
    artifacts: dict[Path, bytes]


def plan_package(root: Path, name: str, kind: str, title: str,
                 bindings: dict[int, dict], order: dict[int, int]) -> BuildPlan:
    package = root / f"improvements/{COURSE_ID}" / name
    journals = load_changes(package)
    manifest_path = package / "manifest.json"
    previous = json.loads(manifest_path.read_bytes()) if manifest_path.exists() else None
    previous_steps = {int(step["step_id"]): step for step in previous["steps"]} if previous else {}
    if previous:
        require(previous.get("course_id") == COURSE_ID and previous.get("base_commit") == BASE_COMMIT,
                f"Unexpected existing manifest identity: {name}")
        require(len(previous_steps) == len(previous["steps"]), f"Duplicate steps in existing manifest: {name}")
    staged, documents, pending = {}, {}, {}
    files = sorted((package / "steps").rglob("*.step"))
    require(bool(files), f"Empty package: {name}")
    for target in files:
        relative = target.relative_to(package / "steps")
        require(len(relative.parts) == 2 and relative.parts[0].isdigit(), f"Invalid staged path: {relative}")
        match = re.fullmatch(r"(\d+)_(\d+)_(text|choice)\.step", relative.name)
        require(match is not None and match.group(3) == kind, f"Unexpected step type/path: {relative}")
        position, sid = int(match.group(1)), int(match.group(2))
        lesson = int(relative.parts[0])
        require(sid not in staged, f"Duplicate staged step: {sid}")
        require(sid in bindings and sid in journals, f"Missing binding or change record: {sid}")
        binding = bindings[sid]
        expected_path = f"steps/{relative.as_posix()}"
        require(binding["lesson_id"] == lesson and binding["position"] == position
                and binding["path"] == expected_path and binding["type"] == kind,
                f"Identity, type or position mismatch: {sid}")
        require(journals[sid].get("path", expected_path) == expected_path, f"Change record path mismatch: {sid}")
        source = root / f"courses/{COURSE_ID}" / expected_path
        baseline = package / "baseline" / relative
        require(not target.is_symlink() and not baseline.is_symlink(), f"Symlink step is unsupported: {sid}")
        if baseline.exists():
            before_bytes = baseline.read_bytes()
        else:
            require(previous is None, f"Missing immutable baseline in existing package: {sid}")
            before_bytes = source.read_bytes()
            pending[baseline] = before_bytes
        after_bytes = target.read_bytes()
        before, after = json.loads(before_bytes), json.loads(after_bytes)
        require(int(before["id"]) == sid and int(after["id"]) == sid
                and before["block"]["name"] == kind and after["block"]["name"] == kind,
                f"Step payload identity mismatch: {sid}")
        fields = allowed_fields(before, after, kind, sid)
        if previous:
            require(sid in previous_steps, f"Existing package cannot acquire a different baseline set: {sid}")
            old = previous_steps[sid]
            require(old["before_file_sha256"] == digest(before_bytes)
                    and old["before_block_sha256"] == block_digest(before["block"]),
                    f"Immutable baseline changed: {sid}")
        staged[sid] = {
            "step_id": sid, "lesson_id": lesson, "position": position,
            "source_path": source.relative_to(root).as_posix(),
            "target_path": target.relative_to(root).as_posix(),
            "baseline_path": baseline.relative_to(root).as_posix(),
            "before_file_sha256": digest(before_bytes), "after_file_sha256": digest(after_bytes),
            "before_block_sha256": block_digest(before["block"]), "after_block_sha256": block_digest(after["block"]),
            "changed_fields": fields, "summary": journals[sid]["summary"],
            "sources": journals[sid]["sources"], "step_url": binding["step_url"],
        }
        documents[sid] = after
    require(set(staged) == set(journals), f"Change records without a unique .step: {sorted(set(journals) - set(staged))}")
    expected_baselines = {Path(step["baseline_path"]).relative_to(package.relative_to(root)) for step in staged.values()}
    actual_baselines = {path.relative_to(package) for path in (package / "baseline").rglob("*.step")}
    require(actual_baselines.issubset(expected_baselines), f"Unexpected baseline files: {name}")
    publication = copy.deepcopy(previous.get("publication", NEW_PUBLICATION) if previous else NEW_PUBLICATION)
    status = "prepared"
    if previous and (publication.get("status") == "verified_on_stepik" or publication.get("applied") or previous.get("status") == "published"):
        require(set(previous_steps) == set(staged), f"Published package membership changed: {name}")
        for sid, step in staged.items():
            require(all(previous_steps[sid].get(field) == step[field] for field in HASH_FIELDS),
                    f"Published package content changed; create a new package instead: {sid}")
        status = previous.get("status", "published")
    manifest = {
        "schema_version": 1, "course_id": COURSE_ID, "date": DATE, "base_commit": BASE_COMMIT,
        "status": status, "changed_steps": len(staged), "changed_lessons": len({step["lesson_id"] for step in staged.values()}),
        "publication": publication, "steps": [staged[sid] for sid in sorted(staged, key=order.__getitem__)],
    }
    return BuildPlan(manifest, pending, {
        manifest_path: json_bytes(manifest),
        package / "CHANGES.md": render_changes(manifest, title),
        package / "preview.html": render_preview(root, manifest, title, documents),
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check generated files and baselines without modifying anything")
    args = parser.parse_args()
    try:
        bindings, order = load_bindings(ROOT)
        # Validate both complete packages before writing either of them.
        plans = [plan_package(ROOT, name, kind, title, bindings, order) for name, kind, title in PACKAGES]
        stale = []
        for plan in plans:
            stale.extend(plan.new_baselines)
            stale.extend(path for path, expected in plan.artifacts.items() if not path.exists() or path.read_bytes() != expected)
        if args.check:
            if stale:
                for path in stale:
                    print(f"Stale or missing: {path.relative_to(ROOT)}", file=sys.stderr)
                return 1
            print("Both course packages are current; no files changed.")
            return 0
        for plan in plans:
            for path, data in plan.new_baselines.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation also prevents a concurrent build from
                # overwriting the first captured version.
                try:
                    with path.open("xb") as output:
                        output.write(data)
                except FileExistsError:
                    require(path.read_bytes() == data, f"Baseline changed during build: {path}")
            for path, data in plan.artifacts.items():
                if not path.exists() or path.read_bytes() != data:
                    path.write_bytes(data)
            manifest = plan.manifest
            print(f"Built {manifest['changed_steps']} steps in {manifest['changed_lessons']} lessons: "
                  f"{next(iter(plan.artifacts)).parent.relative_to(ROOT)}")
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Package build failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
