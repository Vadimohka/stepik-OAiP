#!/usr/bin/env python3
"""Build the course navigation and change index from the current snapshot."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / 'courses/86957'
OUTPUT = COURSE / 'TREE.md'
STEPIK = 'https://stepik.org'

# Use separate publication records so that draft packages never mark a live step.
PACKAGES = [
    ('Первый и второй проходы', 'imports/86957/manifest.json', 'deployment_status'),
    ('Второй проход', 'imports/86957/round2_manifest.json', 'deployment_status'),
    ('Современный C++', 'modernization/86957/manifest.json', 'publication.status'),
    ('Исправление существующих шагов', 'corrections/86957/manifest.json', 'publication.status'),
    ('Качество объяснений и практики', 'improvements/86957/quality-2026-11-23/manifest.json', 'publication.status'),
    ('Согласованное оценивание', 'improvements/86957/assessment-2026-11-23/manifest.json', 'publication.status'),
    ('Функции и контракты', 'improvements/86957/functions-2026-11-23/manifest.json', 'publication.status'),
    ('Задачи на запуск, сортировку и поиск', 'improvements/86957/practice-2026-11-23/manifest.json', 'publication.status'),
    ('Теоретическая редакция', 'improvements/86957/theory-2026-11-23/manifest.json', 'publication.status'),
]


class OpeningText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.done = False

    def handle_endtag(self, tag):
        if tag in {'p', 'h1', 'h2', 'h3', 'li', 'pre', 'div'} and ''.join(self.parts).strip():
            self.done = True

    def handle_data(self, data):
        if not self.done:
            self.parts.append(data)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def label(text):
    return re.sub(r'([\\`*_{}\[\]<>#|])', r'\\\1', ' '.join(text.split()))


def step_description(block):
    parser = OpeningText()
    parser.feed(block.get('text') or '')
    text = ' '.join(''.join(parser.parts).split())
    if len(text) > 94:
        text = text[:94].rsplit(' ', 1)[0] + '…'
    return label(text)


def build():
    bundle = read(COURSE / 'course.json')
    export = read(COURSE / 'manifest.json')
    course = bundle['course']
    maps = {key: {item['id']: item for item in bundle[key]}
            for key in ('sections', 'units', 'lessons', 'step_sources')}
    notes = {}
    for name, path, status_key in PACKAGES:
        package = read(ROOT / path)
        status = package
        for key in status_key.split('.'):
            status = status.get(key, {})
        if status != 'verified_on_stepik':
            continue
        for row in package['steps']:
            notes.setdefault(row['step_id'], []).append(
                f'[{name}](../../{path})')
    bindings = {row['step_id']: row['path'] for row in export['step_files']['bindings']
                if row['status'] == 'exported'}
    steps = maps['step_sources']
    if set(steps) != set(bindings):
        raise ValueError('Снимок и манифест содержат разные наборы шагов')

    out = [
        f'# Дерево курса {course["id"]}', '',
        f'[{label(course["title"])}]({STEPIK}/course/{course["id"]}/syllabus) · [Вычитка](review/index.md)', '',
        f'Модулей {len(maps["sections"])} · уроков {len(maps["lessons"])} · шагов {len(steps)}.', '',
        'Номер задаёт место в уроке. ID закреплён за шагом и служит для сверки при обновлении.',
        'Отметки о правках ведут к манифестам опубликованных пакетов.', '',
    ]
    seen = set()
    for section_id in course['sections']:
        section = maps['sections'][section_id]
        out.extend([f'## {section["position"]}. {label(section["title"])}', ''])
        for unit_id in section['units']:
            unit = maps['units'][unit_id]
            lesson = maps['lessons'][unit['lesson']]
            lesson_id = lesson['id']
            number = f'{section["position"]}.{unit["position"]}'
            out.extend([f'### {number}. {label(lesson["title"])}', '',
                        f'[Урок {lesson_id}]({STEPIK}/lesson/{lesson_id}?unit={unit_id}) · '
                        f'[Текст для вычитки](review/lessons/{lesson_id}.md)', ''])
            for step_id in lesson['steps']:
                step = steps[step_id]
                block = step['block']
                position = step['position']
                path = bindings[step_id]
                if step['lesson'] != lesson_id or not (COURSE / path).is_file():
                    raise ValueError(f'Некорректная привязка шага {step_id}')
                url = f'{STEPIK}/lesson/{lesson_id}/step/{position}?unit={unit_id}'
                line = f'- [{position}. {label(block["name"])}]({url}) · [{step_id}]({path})'
                description = step_description(block)
                if description:
                    line += f' — {description}'
                if step_id in notes:
                    line += ' · ' + ', '.join(notes[step_id])
                out.append(line)
                seen.add(step_id)
            out.append('')
    if seen != set(steps):
        raise ValueError(f'Шаги вне дерева: {sorted(set(steps) - seen)}')
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if TREE.md is stale.')
    args = parser.parse_args()
    content = build()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != content:
            parser.exit(1, 'Дерево устарело. Запустите python3 tools/render_course_tree.py\n')
    else:
        OUTPUT.write_text(content, encoding='utf-8')


if __name__ == '__main__':
    main()
