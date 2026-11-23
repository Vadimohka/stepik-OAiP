#!/usr/bin/env python3
"""Rebuild the structural inventory from author-owned course files.

Run from any directory: python3 improvements/86957/course-review-2026-11-23/summarize.py
No network, learner comments, submissions, or credentials are accessed.
This script counts and indexes evidence. It does not grade pedagogical quality.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COURSE = ROOT / "courses/86957"
ASSESSED = {"choice", "code", "fill-blanks", "string", "table"}
PATTERNS = {
    "outcome_marker": r"\bцел[ьи]\b|научит[её]сь|к концу (?:урока|модуля)|после.{0,55}сможете",
    "practice_marker": r"самопровер|проверьте себя|попробуйте|упражнени|практикум|самостоятельн",
}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Plain(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.images = 0
        self.code_blocks = 0

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        self.images += tag.lower() == "img"
        self.code_blocks += tag.lower() == "pre"


def text_features(block: dict) -> dict:
    parser = Plain()
    parser.feed(block.get("text") or "")
    plain = " ".join(" ".join(parser.parts).split())
    features = {
        "text_character_count": len(plain),
        "image_tag_count": parser.images,
        "pre_tag_count": parser.code_blocks,
    }
    features.update({name: bool(re.search(pattern, plain, re.I)) for name, pattern in PATTERNS.items()})
    return features


def package_records() -> list[dict]:
    paths = [ROOT / "modernization/86957/manifest.json", ROOT / "corrections/86957/manifest.json"]
    paths += sorted((ROOT / "improvements/86957").glob("*/manifest.json"))
    result = []
    for path in paths:
        if not path.exists():
            continue
        data = read(path)
        publication = data.get("publication", {})
        entries = []
        for item in data.get("steps", []):
            if not isinstance(item, dict) or "step_id" not in item:
                continue
            target = ROOT / item.get("target_path", "__not_available__")
            entries.append({
                "step_id": int(item["step_id"]),
                "lesson_id": int(item["lesson_id"]) if item.get("lesson_id") else None,
                "target_path": item.get("target_path"),
                "target_exists": target.is_file(),
                "target_sha256": sha(target) if target.is_file() else None,
            })
        # A correction manifest can document existing snapshots without target files.
        result.append({
            "manifest_path": str(path.relative_to(ROOT)),
            "manifest_sha256": sha(path),
            "status": data.get("status"),
            "publication_status": publication.get("status"),
            "publication_applied": publication.get("applied"),
            "verified_at": publication.get("verified_at"),
            "declared_changed_steps": data.get("changed_steps"),
            "indexed_steps": entries,
        })
    return result


def build() -> dict:
    steps: dict[int, tuple[Path, dict]] = {}
    digest = hashlib.sha256()
    for path in sorted((COURSE / "steps").rglob("*.step")):
        data = read(path)
        sid = int(data["id"])
        if sid in steps:
            raise ValueError(f"Duplicate step ID: {sid}")
        steps[sid] = (path, data)
        digest.update((str(path.relative_to(ROOT)) + "\0" + sha(path) + "\n").encode())

    packages = package_records()
    package_by_step: dict[int, list[dict]] = {}
    for package in packages:
        for entry in package["indexed_steps"]:
            package_by_step.setdefault(entry["step_id"], []).append({
                "manifest_path": package["manifest_path"],
                "publication_status": package["publication_status"],
                "publication_applied": package["publication_applied"],
                **entry,
            })

    referenced = set()
    modules = []
    global_counts = Counter()
    all_correct = []
    no_assessment = []
    course = read(COURSE / "raw/courses/86957.json")
    for section_id in course["sections"]:
        section = read(COURSE / f"raw/sections/{section_id}.json")
        module_counts = Counter()
        lessons = []
        for unit_id in section["units"]:
            unit = read(COURSE / f"raw/units/{unit_id}.json")
            lid = int(unit["lesson"])
            lesson = read(COURSE / f"raw/lessons/{lid}.json")
            lesson_counts = Counter()
            records = []
            for position, step_id in enumerate(lesson["steps"], 1):
                sid = int(step_id)
                path, data = steps[sid]
                if sid in referenced:
                    raise ValueError(f"Step used twice in navigation: {sid}")
                referenced.add(sid)
                block = data["block"]
                kind = block["name"]
                lesson_counts[kind] += 1
                record = {
                    "step_id": sid,
                    "position": position,
                    "type": kind,
                    "path": str(path.relative_to(ROOT)),
                    "sha256": sha(path),
                    "step_url": f"https://stepik.org/lesson/{lid}/step/{position}",
                    "features": text_features(block),
                    "packages": package_by_step.get(sid, []),
                }
                if kind == "choice":
                    source = block.get("source") or {}
                    options = source.get("options") or []
                    option_count = len(options)
                    correct = sum(bool(o.get("is_correct")) for o in options)
                    record["choice_structure"] = {
                        "option_count": option_count,
                        "correct_option_count": correct,
                        "options_with_feedback": sum(bool(o.get("feedback")) for o in options),
                        "has_general_feedback": bool(block.get("feedback_correct") or block.get("feedback_wrong")),
                        "all_options_correct": bool(option_count and correct == option_count),
                    }
                    if record["choice_structure"]["all_options_correct"]:
                        all_correct.append(sid)
                if kind == "code":
                    source = block.get("source") or {}
                    record["code_structure"] = {
                        "source_keys": sorted(source),
                        "template_language_tags": re.findall(r"^::([^\r\n]+)", source.get("templates_data") or "", re.M),
                        "embedded_test_case_count": len(source.get("test_cases") or []),
                        "has_checker_or_generator_source": bool(source.get("code")),
                    }
                # Prepared revisions are indexed individually. Conflicting overlays are
                # reported, never resolved by mtime or silent last-wins precedence.
                prepared = []
                for entry in package_by_step.get(sid, []):
                    if entry["publication_applied"] is False and entry["target_exists"]:
                        revision = read(ROOT / entry["target_path"])
                        prepared.append({
                            "manifest_path": entry["manifest_path"],
                            "target_path": entry["target_path"],
                            "type": revision["block"]["name"],
                            "features": text_features(revision["block"]),
                            "sha256": entry["target_sha256"],
                        })
                record["prepared_revisions"] = prepared
                record["multiple_prepared_revisions"] = len(prepared) > 1
                records.append(record)
            assessed = sum(lesson_counts[k] for k in ASSESSED)
            if not assessed:
                no_assessment.append(lid)
            lessons.append({
                "lesson_id": lid,
                "unit_id": int(unit_id),
                "position": int(unit.get("position", len(lessons) + 1)),
                "title": lesson["title"],
                "step_count": len(records),
                "step_types": dict(sorted(lesson_counts.items())),
                "automatically_assessed_step_count": assessed,
                "has_code_task": bool(lesson_counts["code"]),
                "steps_with_outcome_marker": [r["step_id"] for r in records if r["features"]["outcome_marker"]],
                "text_steps_with_practice_marker": [r["step_id"] for r in records if r["type"] == "text" and r["features"]["practice_marker"]],
                "steps": records,
            })
            module_counts.update(lesson_counts)
        global_counts.update(module_counts)
        modules.append({
            "module_number": int(section["position"]),
            "section_id": int(section_id),
            "title": section["title"],
            "lesson_count": len(lessons),
            "step_count": sum(module_counts.values()),
            "step_types": dict(sorted(module_counts.items())),
            "lessons": lessons,
        })
    missing_from_navigation = sorted(set(steps) - referenced)
    if missing_from_navigation:
        raise ValueError(f"Unreferenced steps: {missing_from_navigation}")
    prepared_ids = sorted({
        r["step_id"] for m in modules for lesson in m["lessons"] for r in lesson["steps"]
        if r["prepared_revisions"]
    })
    return {
        "schema_version": 1,
        "course_id": 86957,
        "review_date": "2026-11-23",
        "source": {
            "navigation": "courses/86957/raw/{courses,sections,units,lessons}",
            "content": "courses/86957/steps/**/*.step",
            "snapshot_digest_sha256": digest.hexdigest(),
            "remote_main_at_review_start": "498e5468863becfdf72f5c73ca52bd2ebfeaf229",
            "live_claim_limit": "Локальный авторский снимок, ранее полученный из Stepik; этот скрипт не проверяет текущий сервер или интерфейс Stepik.",
        },
        "method": {
            "structural_coverage": "Все 485 файлов .step и вся навигация 20 модулей / 62 уроков.",
            "semantic_coverage": "Выборочное экспертное чтение описано в README.md и module_review.json. Инвентаризация не является проверкой корректности каждого предложения или теста.",
            "heuristics": PATTERNS,
            "heuristic_limit": "Найденное слово не доказывает наличие измеримой цели или качественной практики; отсутствие маркера не доказывает отсутствия цели. Число <pre> не равно числу самостоятельных компилируемых примеров. Нет автоматической оценки качества.",
            "assessed_types": sorted(ASSESSED),
            "assessment_limit": "Тип шага означает потенциальное автоматическое оценивание. Он не доказывает валидность ключей, достаточность тестов, обратную связь или соответствие цели урока.",
        },
        "totals": {
            "modules": len(modules),
            "lessons": sum(m["lesson_count"] for m in modules),
            "steps": len(steps),
            "step_types": dict(sorted(global_counts.items())),
            "lessons_without_automatically_assessed_steps": no_assessment,
            "choice_steps_with_all_options_correct": all_correct,
            "prepared_unique_step_count": len(prepared_ids),
            "prepared_unique_step_ids": prepared_ids,
        },
        "packages": packages,
        "modules": sorted(modules, key=lambda m: m["module_number"]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare with saved inventory without modifying it")
    args = parser.parse_args()
    result = build()
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    path = HERE / "inventory.json"
    if args.check:
        if not path.exists() or path.read_text(encoding="utf-8") != serialized:
            print("inventory.json differs; run summarize.py", file=sys.stderr)
            return 1
    else:
        path.write_text(serialized, encoding="utf-8")
    totals = result["totals"]
    print(json.dumps({k: totals[k] for k in ("modules", "lessons", "steps", "step_types", "prepared_unique_step_count")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
