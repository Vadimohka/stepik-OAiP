#!/usr/bin/env python3
"""Create review documents from an already downloaded Stepik course bundle.

Usage: python tools/review_renderer.py courses/86957/course.json

Expected JSON: {"course": {...}, "sections": [...], "units": [...],
                "lessons": [...], "steps": [...], "step_sources": [...]}

Only Python's standard library is used. No network calls, execution of course
code, changes to raw objects, or uploads are performed. Markdown keeps
block.text verbatim (including HTML and code); the optional HTML view filters
active markup and retains an escaped copy of the original text for inspection.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

BASE_URL = "https://stepik.org/"
NOTICE = (
    "Материалы для авторской вычитки. В исходниках source/options и других "
    "полях блоков могут содержаться правильные ответы, скрытые тесты, "
    "проверяющий код и настройки заданий. Эти поля приведены ниже каждого "
    "шага. Полные исходные объекты находятся в raw; читаемые представления "
    "не заменяют исходный экспорт."
)


def identifier(value):
    text = str(value)
    if not re.fullmatch(r"[0-9]+", text):
        raise ValueError(f"Expected a numeric Stepik ID, got {text!r}")
    return text


def entity_map(values):
    if values is None:
        return {}
    if not isinstance(values, list):
        raise ValueError("Entity collections must be JSON arrays")
    result = {}
    for value in values:
        key = identifier(value["id"])
        if key in result and result[key] != value:
            raise ValueError(f"Conflicting objects with ID {key}")
        result[key] = value
    return result


def numeric_position(value, fallback=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return fallback


def md_label(value):
    value = re.sub(r"\s+", " ", str(value)).strip()
    return re.sub(r"([\\`*_{}\[\]<>#|])", r"\\\1", value)


def fenced(value, language="json"):
    if language == "json":
        value = json.dumps(value, ensure_ascii=False, indent=2)
    value = str(value)
    length = max([len(x) for x in re.findall(r"`+", value)] + [2]) + 1
    fence = "`" * max(length, 3)
    return f"{fence}{language}\n{value}\n{fence}\n"


def relative_link(target, document):
    return quote(os.path.relpath(target, document.parent).replace(os.sep, "/"), safe="/-_.")


def safe_url(value):
    value = value.strip()
    if any(ord(c) < 32 for c in value):
        return None
    try:
        scheme = urlsplit(value).scheme.lower()
    except ValueError:
        return None
    if scheme and scheme not in {"https", "http", "mailto"}:
        return None
    return value if value.startswith("#") else urljoin(BASE_URL, value)


class StaticHTML(HTMLParser):
    """Keep readable HTML and whitespace; omit executable/active markup."""

    tags = set("p div span br hr pre code kbd samp var b strong i em u s del ins "
               "sub sup mark small h1 h2 h3 h4 h5 h6 ul ol li dl dt dd blockquote "
               "table caption thead tbody tfoot tr th td a img figure figcaption "
               "details summary math mrow mi mn mo mtext msup msub mfrac msqrt "
               "semantics annotation".split())
    voids = {"br", "hr", "img"}
    suppressed = {"script", "style", "iframe", "object", "embed", "template", "noscript"}
    attrs = {"alt", "title", "width", "height", "colspan", "rowspan", "scope",
             "start", "reversed", "type", "open", "display", "encoding"}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []
        self.hidden = []
        self.open_tags = []

    def handle_starttag(self, tag, attrs):
        if self.hidden:
            if tag in self.suppressed and tag != "embed":
                self.hidden.append(tag)
            return
        if tag in self.suppressed:
            values = dict(attrs)
            source = safe_url(values.get("src", "")) if values.get("src") else None
            if source:
                self.parts.append('<p class="embedded"><a href="' + html.escape(source, quote=True)
                                  + '">Встроенный материал: ' + html.escape(source) + '</a></p>')
            if tag != "embed":
                self.hidden.append(tag)
            return
        if tag not in self.tags:
            return
        cleaned = []
        for name, value in attrs:
            if value is None:
                if name in {"open", "reversed"}:
                    cleaned.append(name)
                continue
            if name in self.attrs:
                cleaned.append(f'{name}="{html.escape(value, quote=True)}"')
            elif (tag == "a" and name == "href") or (tag == "img" and name == "src"):
                value = safe_url(value)
                if value:
                    cleaned.append(f'{name}="{html.escape(value, quote=True)}"')
        suffix = " " + " ".join(cleaned) if cleaned else ""
        self.parts.append(f"<{tag}{suffix}>")
        if tag not in self.voids:
            self.open_tags.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.voids and tag != "embed":
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag in self.open_tags:
            while self.open_tags:
                current = self.open_tags.pop()
                self.parts.append(f"</{current}>")
                if current == tag:
                    break

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(html.escape(data, quote=False))

    def handle_entityref(self, name):
        if not self.hidden:
            self.parts.append(f"&{name};")

    def handle_charref(self, name):
        if not self.hidden:
            self.parts.append(f"&#{name};")

    def result(self):
        return "".join(self.parts) + "".join(f"</{tag}>" for tag in reversed(self.open_tags))


def readable_html(text):
    parser = StaticHTML()
    parser.feed(text)
    parser.close()
    return parser.result()


def build_documents(bundle, source_root, output_dir):
    """Return ({Path: UTF-8 text}, statistics), without writing any files."""
    source_root, output_dir = Path(source_root), Path(output_dir)
    course = bundle["course"]
    course_id = identifier(course["id"])
    title = course.get("title") or f"Курс {course_id}"
    maps = {key: entity_map(bundle.get(key, [])) for key in
            ("sections", "units", "lessons", "steps", "step_sources")}
    sections, units, lessons, steps, sources = (maps[key] for key in maps)
    errors = []
    placements = defaultdict(list)
    structure = []

    def ordered_ids(parent, field, collection, relation=None, parent_id=None):
        if field in parent and isinstance(parent[field], list):
            return [identifier(x) for x in parent[field]]
        matches = [obj for obj in collection.values()
                   if relation is None or str(obj.get(relation)) == str(parent_id)]
        matches.sort(key=lambda x: (numeric_position(x.get("position")), int(x["id"])))
        return [identifier(x["id"]) for x in matches]

    section_ids = ordered_ids(course, "sections", sections, "course", course_id)
    for section_number, sid in enumerate(section_ids, 1):
        section = sections.get(sid)
        if section is None:
            errors.append(f"Отсутствует раздел {sid}.")
            section = {"id": sid, "title": f"Раздел {sid} — объект отсутствует"}
        snum = section.get("position", section_number)
        children = []
        for unit_number, uid in enumerate(ordered_ids(section, "units", units, "section", sid), 1):
            unit = units.get(uid)
            if unit is None:
                errors.append(f"Отсутствует unit {uid} в разделе {sid}.")
                continue
            lid = identifier(unit["lesson"])
            lesson = lessons.get(lid)
            if lesson is None:
                errors.append(f"Отсутствует урок {lid} (unit {uid}).")
                lesson = {"id": lid, "title": f"Урок {lid} — объект отсутствует"}
            label = f"{snum}.{unit.get('position', unit_number)}"
            placement = {"number": label, "unit": uid, "section": sid, "lesson": lid,
                         "title": lesson.get("title") or f"Урок {lid}"}
            children.append(placement)
            placements[lid].append(placement)
        structure.append((section, snum, children))

    for lid, lesson in lessons.items():
        if lid not in placements:
            placements[lid].append({"number": "—", "unit": None, "section": None,
                                    "lesson": lid, "title": lesson.get("title") or f"Урок {lid}"})

    lesson_steps = {}
    all_known_steps = {**steps, **sources}
    for lid in placements:
        lesson = lessons.get(lid, {"id": lid})
        lesson_steps[lid] = ordered_ids(lesson, "steps", all_known_steps, "lesson", lid)
    referenced_steps = {sid for ids in lesson_steps.values() for sid in ids}
    missing_steps = sorted(sid for sid in referenced_steps if sid not in all_known_steps)
    missing_sources = sorted(sid for sid in referenced_steps if sid not in sources)
    unplaced_steps = sorted(set(all_known_steps) - referenced_steps)
    if missing_steps:
        errors.append("Не получены объекты шагов: " + ", ".join(missing_steps) + ".")
    if missing_sources:
        errors.append("Нет авторских step-sources для шагов: " + ", ".join(missing_sources) + ".")
    if unplaced_steps:
        errors.append("Есть шаги вне списков уроков; см. raw: " + ", ".join(unplaced_steps) + ".")

    stats = {"course_id": course_id, "sections": len(section_ids), "units": len(units),
             "lessons": len(placements), "steps": len(referenced_steps),
             "step_sources": len(sources), "missing_steps": missing_steps,
             "missing_step_sources": missing_sources, "unplaced_steps": unplaced_steps,
             "warnings": errors}
    docs = {}
    index_file, course_file = output_dir / "index.md", output_dir / "course.md"
    heading = f"# {md_label(title)}\n\n{NOTICE}\n\n"
    heading += f"[Курс на Stepik]({BASE_URL}course/{course_id}) · ID: {course_id}\n\n"
    heading += (f"Разделов: {stats['sections']}; уроков: {stats['lessons']}; "
                f"шагов в структуре: {stats['steps']}; авторских исходников: {len(sources)}.\n\n")
    if errors:
        heading += "## Неполнота или особенности экспорта\n\n" + "".join(f"- {e}\n" for e in errors) + "\n"
    index_parts = [heading, "[Весь курс одним файлом](course.md) · [HTML для чтения](course.html)\n\n"]
    course_parts = [heading, "[Оглавление](index.md) · [HTML для чтения](course.html)\n\n"]
    html_parts = [f"<h1>{html.escape(str(title))}</h1><p>{html.escape(NOTICE)}</p>",
                  f'<p><a href="{BASE_URL}course/{course_id}">Курс на Stepik</a></p>']
    if errors:
        html_parts += ["<h2>Неполнота или особенности экспорта</h2><ul>",
                       "".join(f"<li>{html.escape(e)}</li>" for e in errors), "</ul>"]

    def step_view(sid, lid, unit_id, fallback_position, document, level):
        step, source = steps.get(sid, {}), sources.get(sid)
        record = source if source is not None else step
        block = record.get("block") or {}
        display_block = step.get("block") or {}
        position = record.get("position", step.get("position", fallback_position))
        name = block.get("name") or display_block.get("name") or "неизвестный тип"
        text = block.get("text", display_block.get("text", "")) or ""
        if not isinstance(text, str):
            text = json.dumps(text, ensure_ascii=False, indent=2)
        url = f"{BASE_URL}lesson/{lid}/step/{position}"
        if unit_id is not None:
            url += "?unit=" + str(unit_id)
        step_title = f"Шаг {position} — {name} (ID {sid})"
        links = [f"[Открыть на Stepik]({url})"]
        if source is not None:
            links.append("[Исходник step-source](" + relative_link(source_root / "raw" / "step-sources" / f"{sid}.json", document) + ")")
        if step:
            links.append("[Объект step](" + relative_link(source_root / "raw" / "steps" / f"{sid}.json", document) + ")")
        md = [f"{'#' * level} {md_label(step_title)}\n\n", " · ".join(links) + "\n\n"]
        body = [f"<section><h4>{html.escape(step_title)}</h4><p><a href=\"{html.escape(url, quote=True)}\">Открыть на Stepik</a></p>"]
        if source is None:
            message = "Авторский step-source отсутствует: ответы, тесты и настройки могут быть неполными."
            md.append(f"> {message}\n\n")
            body.append(f"<p><strong>{message}</strong></p>")
        if not record:
            md.append("Объект шага отсутствует в выгрузке.\n\n")
            body.append("<p>Объект шага отсутствует в выгрузке.</p>")
        elif text:
            # Deliberately do not strip/reformat text: code whitespace is significant.
            md.append(text + "\n\n")
            body.append('<div class="step-text">' + readable_html(text) + '</div>')
            body.append('<details><summary>Исходный HTML/текст блока</summary><pre><code>'
                        + html.escape(text) + '</code></pre></details>')
        else:
            md.append("Текст блока пуст; содержимое шага приведено в полях ниже.\n\n")
        config = {key: value for key, value in block.items() if key != "text"}
        if config:
            md.append("<details>\n<summary>Ответы, тесты, медиа и настройки блока</summary>\n\n"
                      + fenced(config) + "\n</details>\n\n")
            body.append('<details><summary>Ответы, тесты, медиа и настройки блока</summary><pre><code>'
                        + html.escape(json.dumps(config, ensure_ascii=False, indent=2)) + '</code></pre></details>')
        video = block.get("video")
        if not isinstance(video, dict):
            video = display_block.get("video")
        if isinstance(video, dict):
            video_links = []
            for item in video.get("urls") or []:
                if not isinstance(item, dict) or not isinstance(item.get("url"), str):
                    continue
                video_url = safe_url(item["url"])
                if video_url:
                    video_links.append((str(item.get("quality") or "видео"), video_url))
            if video_links:
                md.append("Видео: " + " · ".join(
                    f"[{md_label(quality)}](<{video_url}>)" for quality, video_url in video_links) + "\n\n")
                body.append("<p>Видео: " + " · ".join(
                    f'<a href="{html.escape(video_url, quote=True)}">{html.escape(quality)}</a>'
                    for quality, video_url in video_links) + "</p>")
        # Preserve extra/resolved display fields separately from author settings.
        extra = {key: value for key, value in display_block.items()
                 if key != "text" and (key not in block or value != block[key])}
        if extra:
            md.append("<details>\n<summary>Дополнительные поля представления step</summary>\n\n"
                      + fenced(extra) + "\n</details>\n\n")
            body.append('<details><summary>Дополнительные поля представления step</summary><pre><code>'
                        + html.escape(json.dumps(extra, ensure_ascii=False, indent=2)) + '</code></pre></details>')
        body.append("</section>")
        return "".join(md), "".join(body)

    def render_lesson(placement, document, level=3):
        lid = placement["lesson"]
        lesson_heading = f"{placement['number']}. {placement['title']}"
        md = [f"{'#' * level} {md_label(lesson_heading)}\n\n", f"Урок: {lid}"]
        if placement["unit"]:
            md.append(f" · unit: {placement['unit']}")
        md.append("\n\n")
        body = [f"<h3>{html.escape(lesson_heading)}</h3><p>Урок: {lid}</p>"]
        for fallback, sid in enumerate(lesson_steps[lid], 1):
            step_md, step_html = step_view(sid, lid, placement["unit"], fallback, document, level + 1)
            md.append(step_md)
            body.append(step_html)
        if not lesson_steps[lid]:
            md.append("В полученном объекте урока нет шагов.\n\n")
            body.append("<p>В полученном объекте урока нет шагов.</p>")
        return "".join(md), "".join(body)

    for section, number, children in structure:
        section_title = f"{number}. {section.get('title') or 'Без названия'}"
        index_parts.append(f"## {md_label(section_title)}\n\n")
        course_parts.append(f"## {md_label(section_title)}\n\n")
        html_parts.append(f"<h2>{html.escape(section_title)}</h2>")
        for placement in children:
            lid = placement["lesson"]
            index_parts.append(f"- [{md_label(placement['number'] + '. ' + placement['title'])}](lessons/{lid}.md) "
                               f"— {len(lesson_steps[lid])} шагов; урок {lid}; unit {placement['unit']}\n")
            md, rendered = render_lesson(placement, course_file)
            course_parts.append(md)
            html_parts.append(rendered)
        index_parts.append("\n")
    orphans = [ps[0] for ps in placements.values() if ps[0]["unit"] is None]
    if orphans:
        orphan_heading = "Уроки без размещения в структуре курса"
        index_parts.append(f"## {orphan_heading}\n\n")
        course_parts.append(f"## {orphan_heading}\n\n")
        html_parts.append(f"<h2>{orphan_heading}</h2>")
        for placement in orphans:
            lid = placement["lesson"]
            index_parts.append(f"- [{md_label(placement['title'])}](lessons/{lid}.md) — урок {lid}\n")
            md, rendered = render_lesson(placement, course_file)
            course_parts.append(md)
            html_parts.append(rendered)

    for lid, places in placements.items():
        document = output_dir / "lessons" / f"{lid}.md"
        md = [f"# {md_label(places[0]['title'])}\n\n{NOTICE}\n\n",
              "[Оглавление](../index.md) · [Весь курс](../course.md)\n\n",
              "Расположение в курсе: " + "; ".join(
                  f"{p['number']} (unit {p['unit']})" if p["unit"] else "не указано" for p in places) + ".\n\n"]
        content, _ = render_lesson(places[0], document, level=2)
        md.append(content)
        docs[document] = "".join(md)
    docs[index_file] = "".join(index_parts)
    docs[course_file] = "".join(course_parts)
    csp = "default-src 'none'; img-src https: http:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"
    css = "body{max-width:1000px;margin:2em auto;padding:0 1em;font:17px/1.6 system-ui;color:#17202a}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:1em}code{font-family:monospace}img{max-width:100%;height:auto}table{border-collapse:collapse}td,th{border:1px solid #bcc;padding:.35em}section{border-top:1px solid #bbb;padding:1em 0}details{margin:1em 0}summary{cursor:pointer}h2{margin-top:2em}a{color:#145da0}.step-text h1{font-size:1.4em}.step-text h2{font-size:1.3em}"
    docs[output_dir / "course.html"] = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta http-equiv="Content-Security-Policy" content="{html.escape(csp, quote=True)}">'
        f"<title>{html.escape(str(title))}</title><style>{css}</style></head><body>"
        + "\n".join(html_parts) + "</body></html>\n"
    )
    return docs, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("course_json", type=Path)
    parser.add_argument("--output", type=Path, help="Default: <course.json parent>/review")
    args = parser.parse_args()
    source = args.course_json.resolve()
    output = args.output.resolve() if args.output else source.parent / "review"
    with source.open(encoding="utf-8") as stream:
        bundle = json.load(stream)
    documents, stats = build_documents(bundle, source.parent, output)
    for path, content in documents.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(json.dumps({"files_written": len(documents), "output": str(output), **stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
