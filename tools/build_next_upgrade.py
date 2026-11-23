#!/usr/bin/env python3
"""Build the functions and practice upgrade against commit 498e546; no network writes.

Immutable baselines preserve every replaced task, including its original tests.
The builder validates both complete packages before writing either one.
"""
from __future__ import annotations

import argparse
import copy
import html
import json
from pathlib import Path
import re
import sys

from build_quality_packages import (BuildPlan, CSS, HASH_FIELDS, NEW_PUBLICATION,
                                    allowed_fields as previous_allowed_fields,
                                    block_digest, changed_fields, digest, json_bytes,
                                    load_bindings, load_changes, publication_note,
                                    require, text_only)

ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = 86957
BASE_COMMIT = '498e5468863becfdf72f5c73ca52bd2ebfeaf229'
DATE = '2026-11-23'
PACKAGES = (
    ('functions-2026-11-23', {'text'}, 'Функции: интерфейсы, контракты и границы'),
    ('practice-2026-11-23', {'choice', 'code'}, 'Практика: запуск C++, сортировка и поиск'),
)


def allowed_fields(before: dict, after: dict, kind: str, sid: int) -> list[str]:
    if kind in {'text', 'choice'}:
        return previous_allowed_fields(before, after, kind, sid)
    fields = changed_fields(before, after)
    require(bool(fields), f'Unchanged code step: {sid}')
    require(sid in {4643238, 4734985, 3496826}, f'Unreviewed code-step scope: {sid}')
    if sid == 4643238:
        allowed = {
            'block.text', 'block.source.templates_data',
            'block.options.limits.c++', 'block.options.code_templates.c++',
            'block.options.code_templates_header_lines_count.c++',
            'block.options.code_templates_footer_lines_count.c++',
        }
        require(set(fields) == allowed, f'Unexpected entry change: {fields}')
        require(after['block']['options']['limits']['c++'] == before['block']['options']['limits']['c'],
                'Entry C++ limits differ from preserved C limits')
    else:
        def permitted(field):
            return (field in {'block.text', 'block.feedback_correct', 'block.feedback_wrong',
                             'block.source.code', 'block.source.test_cases'}
                    or field == 'block.options.samples' or field.startswith('block.options.samples['))
        require(all(permitted(field) for field in fields), f'Unexpected code task change: {sid}: {fields}')
        require({'block.text', 'block.source.code', 'block.source.test_cases'}.issubset(fields),
                f'Incomplete task replacement: {sid}')
        require(after['block']['source']['test_cases'] == [], f'Generated tests duplicated in export: {sid}')
    return fields


def render_changes(manifest: dict, title: str) -> bytes:
    lines = [f'# {title}', '', f'Дата: {DATE}. Базовый коммит: `{BASE_COMMIT}`.', '',
             publication_note(manifest), '',
             f'Изменено **{manifest["changed_steps"]} шагов в {manifest["changed_lessons"]} уроках**. '
             'ID, типы и размещение сохранены. Исходные файлы, в том числе прежние задачи и тесты, находятся в `baseline/steps/`.', '',
             '[Превью](preview.html) · [Манифест и точные изменённые поля](manifest.json)', '',
             '| Шаг | Урок / позиция | Изменение |', '| --- | --- | --- |']
    for step in manifest['steps']:
        summary = step['summary'].replace('|', '\\|').replace('\n', ' ')
        lines.append(f'| [{step["step_id"]}]({step["step_url"]}) | {step["lesson_id"]} / {step["position"]} | {summary} |')
    lines += ['', '## Воспроизводимость', '',
              '`python3 tools/build_next_upgrade.py --check` проверяет базовые копии, привязки, '
              'манифесты и превью без изменения файлов. `python3 tools/verify_next_upgrade.py` '
              'проверяет примеры и авторские проверяющие программы.', '',
              'Локальные проверки не воспроизводят серверное оценивание Stepik. '
              'Публикация и область проверки через API указаны в манифесте; реальные попытки и начисление баллов не проверялись.', '']
    return '\n'.join(lines).encode('utf-8')


def render_preview(package: Path, manifest: dict, title: str, documents: dict[int, dict]) -> bytes:
    esc = html.escape
    parts = ['<!doctype html>', '<html lang="ru"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             f'<title>{esc(title)}</title><style>{CSS}</style></head><body>',
             f'<header id="top"><h1>{esc(title)}</h1><p>Курс {COURSE_ID} · {DATE} · '
             f'{manifest["changed_steps"]} шагов в {manifest["changed_lessons"]} уроках</p>',
             f'<p class="notice">{esc(publication_note(manifest))}</p>',
             '<p><a href="README.md">Описание</a> · <a href="manifest.json">Манифест</a> · '
             '<a href="CHANGES.md">Изменения</a></p></header><div class="layout">',
             '<nav aria-label="Шаги пакета"><h2>Навигация</h2><ol>']
    for step in manifest['steps']:
        body = documents[step['step_id']]['block']['text']
        heading = re.search(r'<h[1-6](?:\s[^>]*)?>(.*?)</h[1-6]>', body, re.S | re.I)
        label = text_only(heading.group(1)) if heading else step['summary']
        parts.append(f'<li><a href="#step-{step["step_id"]}">{esc(label)}</a>'
                     f'<br><span class="meta">ID {step["step_id"]} · {step["lesson_id"]}/{step["position"]}</span></li>')
    parts.append('</ol></nav><main>')
    for step in manifest['steps']:
        sid = step['step_id']
        block = documents[sid]['block']
        target = (ROOT / step['target_path']).relative_to(package).as_posix()
        baseline = (ROOT / step['baseline_path']).relative_to(package).as_posix()
        parts += [f'<article id="step-{sid}"><div class="article-heading">',
                  f'<p class="meta">ID {sid} · урок {step["lesson_id"]} · позиция {step["position"]}</p>',
                  f'<p>{esc(step["summary"])}</p><p><a href="{esc(step["step_url"], quote=True)}">Шаг на Stepik</a> · '
                  f'<a href="{esc(target, quote=True)}">Новая версия</a> · '
                  f'<a href="{esc(baseline, quote=True)}">Исходная версия</a></p></div>', block['text']]
        if block['name'] == 'choice':
            options = block['source']['options']
            parts.append('<ol class="choices">')
            parts.extend(f'<li>{option["text"]}</li>' for option in options)
            parts += ['</ol><details class="teacher"><summary>Преподавателю: ключ и обратная связь</summary>',
                      '<p>Авторский порядок; перемешивание на платформе сохранено. '
                      'Здесь не моделируется начисление баллов Stepik.</p><ol>']
            for option in options:
                verdict = 'Верно' if option['is_correct'] else 'Неверно'
                parts.append(f'<li><strong>{verdict}.</strong> {option["text"]}'
                             f'<div class="feedback">{option["feedback"]}</div></li>')
            parts.append('</ol>')
            for name in ('feedback_correct', 'feedback_wrong'):
                if block.get(name):
                    parts.append(f'<p>{block[name]}</p>')
            parts.append('</details>')
        elif block['name'] == 'code':
            options = block['options']
            parts.append('<h3>Примеры ввода и вывода</h3><table><thead><tr><th>Ввод</th><th>Вывод</th></tr></thead><tbody>')
            for dataset, reply in options['samples']:
                parts.append(f'<tr><td><pre>{esc(dataset)}</pre></td><td><pre>{esc(reply)}</pre></td></tr>')
            parts += ['</tbody></table><details class="teacher"><summary>Преподавателю: настройки задачи</summary>',
                      f'<p>Языки: {esc(", ".join(options["code_templates"]))}. '
                      f'Лимит времени: {options["execution_time_limit"]} с; '
                      f'лимит памяти: {options["execution_memory_limit"]} МиБ. '
                      'Серверное выполнение в этом превью не проверяется.</p>', '</details>']
        parts.append('<div class="sources"><strong>Справочные источники</strong><ul>')
        parts.extend(f'<li><a href="{esc(url, quote=True)}">{esc(url)}</a></li>' for url in step['sources'])
        parts.append('</ul><p><a href="#top">К началу пакета</a></p></div></article>')
    parts.append('</main></div></body></html>\n')
    return '\n'.join(parts).encode('utf-8')


def plan_package(name: str, kinds: set[str], title: str, bindings: dict, order: dict) -> BuildPlan:
    package = ROOT / f'improvements/{COURSE_ID}' / name
    journals = load_changes(package)
    manifest_path = package / 'manifest.json'
    previous = json.loads(manifest_path.read_bytes()) if manifest_path.exists() else None
    previous_steps = {int(step['step_id']): step for step in previous['steps']} if previous else {}
    if previous:
        require(previous.get('course_id') == COURSE_ID and previous.get('base_commit') == BASE_COMMIT,
                f'Unexpected existing manifest identity: {name}')
        require(len(previous_steps) == len(previous['steps']), f'Duplicate existing steps: {name}')
    staged, documents, pending = {}, {}, {}
    for target in sorted((package / 'steps').glob('*/*.step')):
        relative = target.relative_to(package)
        match = re.fullmatch(r'steps/(\d+)/(\d+)_(\d+)_(text|choice|code)\.step', relative.as_posix())
        require(match is not None, f'Invalid path: {relative}')
        lesson, position, sid = map(int, match.groups()[:3])
        kind = match.group(4)
        require(kind in kinds and sid not in staged, f'Unexpected or duplicate step: {relative}')
        require(sid in bindings and sid in journals, f'Missing binding or change record: {sid}')
        binding = bindings[sid]
        require(binding['lesson_id'] == lesson and binding['position'] == position
                and binding['path'] == relative.as_posix() and binding['type'] == kind,
                f'Binding mismatch: {sid}')
        require(journals[sid].get('path', relative.as_posix()) == relative.as_posix(),
                f'Journal path mismatch: {sid}')
        source = ROOT / f'courses/{COURSE_ID}' / relative
        baseline = package / 'baseline' / relative
        require(not target.is_symlink() and not baseline.is_symlink(), f'Symlink step: {sid}')
        if baseline.exists():
            before_bytes = baseline.read_bytes()
        else:
            require(previous is None, f'Missing immutable baseline: {sid}')
            before_bytes = source.read_bytes()
            pending[baseline] = before_bytes
        after_bytes = target.read_bytes()
        before, after = json.loads(before_bytes), json.loads(after_bytes)
        require(int(before['id']) == sid and int(after['id']) == sid
                and before['block']['name'] == kind and after['block']['name'] == kind,
                f'Payload identity mismatch: {sid}')
        fields = allowed_fields(before, after, kind, sid)
        if previous:
            require(sid in previous_steps, f'Changed baseline membership: {sid}')
            old = previous_steps[sid]
            require(old['before_file_sha256'] == digest(before_bytes)
                    and old['before_block_sha256'] == block_digest(before['block']),
                    f'Immutable baseline changed: {sid}')
        staged[sid] = {
            'step_id': sid, 'lesson_id': lesson, 'position': position,
            'source_path': source.relative_to(ROOT).as_posix(),
            'target_path': target.relative_to(ROOT).as_posix(),
            'baseline_path': baseline.relative_to(ROOT).as_posix(),
            'before_file_sha256': digest(before_bytes), 'after_file_sha256': digest(after_bytes),
            'before_block_sha256': block_digest(before['block']), 'after_block_sha256': block_digest(after['block']),
            'changed_fields': fields, 'summary': journals[sid]['summary'],
            'sources': journals[sid]['sources'], 'step_url': binding['step_url'],
        }
        if kind == 'code':
            staged[sid]['assessment_semantics'] = 'preserved' if sid == 4643238 else 'replaced'
        documents[sid] = after
    require(staged and set(staged) == set(journals), f'Journal/step membership mismatch: {name}')
    expected = {ROOT / step['baseline_path'] for step in staged.values()}
    actual = set((package / 'baseline').rglob('*.step'))
    require(actual.issubset(expected), f'Unexpected baseline files: {name}')
    if previous:
        require(set(previous_steps) == set(staged), f'Changed immutable package membership: {name}')
    publication = copy.deepcopy(previous.get('publication', NEW_PUBLICATION) if previous else NEW_PUBLICATION)
    status = 'prepared'
    if previous and (publication.get('applied') or publication.get('status') == 'verified_on_stepik'
                     or previous.get('status') == 'published'):
        for sid, step in staged.items():
            require(all(previous_steps[sid].get(field) == step[field] for field in HASH_FIELDS),
                    f'Published content changed; create another package: {sid}')
        status = previous.get('status', 'published')
    manifest = {
        'schema_version': 1, 'course_id': COURSE_ID, 'date': DATE, 'base_commit': BASE_COMMIT,
        'status': status, 'changed_steps': len(staged),
        'changed_lessons': len({step['lesson_id'] for step in staged.values()}),
        'publication': publication,
        'dependencies': (['improvements/86957/quality-2026-11-23/manifest.json']
                         if name.startswith('practice-') else []),
        'steps': [staged[sid] for sid in sorted(staged, key=order.__getitem__)],
    }
    return BuildPlan(manifest, pending, {
        manifest_path: json_bytes(manifest),
        package / 'CHANGES.md': render_changes(manifest, title),
        package / 'preview.html': render_preview(package, manifest, title, documents),
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only stale-artifact check')
    args = parser.parse_args()
    try:
        bindings, order = load_bindings(ROOT)
        plans = [plan_package(name, kinds, title, bindings, order) for name, kinds, title in PACKAGES]
        stale = []
        for plan in plans:
            stale.extend(plan.new_baselines)
            stale.extend(path for path, data in plan.artifacts.items()
                         if not path.exists() or path.read_bytes() != data)
        if args.check:
            for path in stale:
                print(f'Stale or missing: {path.relative_to(ROOT)}', file=sys.stderr)
            if stale:
                return 1
            print('Functions and practice packages are current; no files changed.')
            return 0
        for plan in plans:
            for path, data in plan.new_baselines.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with path.open('xb') as output:
                        output.write(data)
                except FileExistsError:
                    require(path.read_bytes() == data, f'Baseline changed during build: {path}')
            for path, data in plan.artifacts.items():
                if not path.exists() or path.read_bytes() != data:
                    path.write_bytes(data)
            print(f'Built {plan.manifest["changed_steps"]} steps: {next(iter(plan.artifacts)).parent.relative_to(ROOT)}')
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f'Upgrade build failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
