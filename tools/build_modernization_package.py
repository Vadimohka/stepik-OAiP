#!/usr/bin/env python3
"""Build the reviewed text-only course revision without contacting Stepik."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'modernization/86957'
BASE_COMMIT = '16a2f9d2b42c33a4f8b50cfa25e1e424fc96fc9d'
DATE = '2026-11-23'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def block_digest(block: dict) -> str:
    return digest(json.dumps(block, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode('utf-8'))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def safe_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Path escapes repository')
    return path


def build() -> dict:
    journals = {}
    for journal in sorted(OUT.glob('*_changes.json')):
        payload = json.loads(journal.read_text(encoding='utf-8'))
        for change in payload['changes']:
            sid = int(change['step_id'])
            if sid in journals:
                raise ValueError(f'Duplicate change record: {sid}')
            journals[sid] = change
    bindings = {int(item['step_id']): item for item in json.loads(
        (ROOT / 'courses/86957/manifest.json').read_text(encoding='utf-8'))['step_files']['bindings']}
    steps = []
    for target in sorted((OUT / 'steps').glob('*/*.step')):
        match = re.fullmatch(r'(\d+)_(\d+)_text\.step', target.name)
        if not match:
            raise ValueError(f'Only existing text steps are allowed: {target.name}')
        position, sid = map(int, match.groups())
        lesson = int(target.parent.name)
        source = ROOT / 'courses/86957/steps' / str(lesson) / target.name
        baseline = OUT / 'baseline' / str(lesson) / target.name
        # Once captured, the baseline is immutable even after a future live sync.
        before_bytes = baseline.read_bytes() if baseline.exists() else source.read_bytes()
        after_bytes = target.read_bytes()
        before, after = json.loads(before_bytes), json.loads(after_bytes)
        restored = json.loads(after_bytes)
        restored['block']['text'] = before['block']['text']
        if restored != before or before['block']['name'] != 'text' or int(after['id']) != sid:
            raise ValueError(f'Change outside block.text: {sid}')
        if after['block']['text'] == before['block']['text']:
            raise ValueError(f'Unchanged staged step: {sid}')
        binding = bindings[sid]
        if binding['lesson_id'] != lesson or binding['position'] != position:
            raise ValueError(f'Identity or position mismatch: {sid}')
        baseline.parent.mkdir(parents=True, exist_ok=True)
        if not baseline.exists():
            baseline.write_bytes(before_bytes)
        change = journals.pop(sid)
        summary = next((change[key] for key in ('summary', 'rationale', 'goal', 'title')
                        if change.get(key)), 'Обновление объяснения и практики')
        steps.append(dict(step_id=sid, lesson_id=lesson, position=position,
            source_path=str(source.relative_to(ROOT)), target_path=str(target.relative_to(ROOT)),
            baseline_path=str(baseline.relative_to(ROOT)),
            before_block_sha256=block_digest(before['block']),
            after_block_sha256=block_digest(after['block']),
            before_file_sha256=digest(before_bytes), after_file_sha256=digest(after_bytes),
            step_url=binding['step_url'], summary=summary, sources=change.get('sources', [])))
    if journals or not steps:
        raise ValueError(f'Unmatched change records or empty package: {sorted(journals)}')
    manifest = dict(schema_version=1, course_id=86957, date=DATE, base_commit=BASE_COMMIT,
                    status='prepared', changed_fields=['block.text'], changed_steps=len(steps),
                    changed_lessons=len({s['lesson_id'] for s in steps}),
                    publication=dict(status='blocked_http_403', applied=False,
                        note='An authenticated access attempt returned HTTP 403. No course content mutation was sent.'),
                    steps=steps)
    write_json(OUT / 'manifest.json', manifest)
    lines = ['# Изменения: первый пакет модернизации C++', '',
             f'Дата: {DATE}. Основа: `{BASE_COMMIT}`.', '',
             f'Подготовлено {len(steps)} текстовых шага в {manifest["changed_lessons"]} уроках. '
             'Пакет не опубликован на Stepik: авторизованный доступ вернул HTTP 403.', '',
             'Изменено только поле `block.text`. Идентификаторы, расположение и оценочные задания сохранены.', '',
             '| Урок / шаг | ID | Изменение |', '|---|---:|---|']
    for step in steps:
        summary = step['summary'].replace('|', '\\|').replace('\n', ' ')
        lines.append(f'| [{step["lesson_id"]} / {step["position"]}]({step["step_url"]}) '
                     f'| {step["step_id"]} | {summary} |')
    (OUT / 'CHANGES.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    preview = ['<!doctype html><html lang="ru"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>ОАиП — пакет модернизации C++</title>',
        '<style>body{max-width:1000px;margin:2rem auto;padding:0 1rem;font:18px/1.6 system-ui;color:#162b38;background:#fbfaf7}'
        'h1,h2,h3{line-height:1.25}section{margin:3rem 0;border-top:3px solid #176660;padding-top:1rem}'
        'pre{overflow:auto;background:#edf1f4;padding:1rem;border-radius:8px;font-size:14px;line-height:1.5}'
        'code{font-size:.9em}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd4d8;padding:.6rem;text-align:left;vertical-align:top}'
        'a{color:#11645e}.notice{background:#fff0c7;padding:1rem}nav li{margin:.4rem 0}</style>',
        '<h1>Основы алгоритмизации и программирования: современный C++</h1>',
        '<p class="notice">Подготовленная редакция. На Stepik ещё не опубликована: авторизованный доступ вернул HTTP 403.</p>',
        '<p>Существующие ID и позиции сохранены. Ниже показаны только новые тексты; исходные варианты лежат в baseline/.</p><nav><ol>']
    for step in steps:
        preview.append(f'<li><a href="#step-{step["step_id"]}">Урок {step["lesson_id"]}, '
                       f'шаг {step["position"]}: {html.escape(step["summary"])}</a></li>')
    preview.append('</ol></nav>')
    for step in steps:
        text = json.loads(safe_path(step['target_path']).read_text(encoding='utf-8'))['block']['text']
        preview.extend([f'<section id="step-{step["step_id"]}"><h2>Урок {step["lesson_id"]}, '
                        f'шаг {step["position"]} · ID {step["step_id"]}</h2>',
                        f'<p><a href="{html.escape(step["step_url"], quote=True)}">Текущая версия на Stepik</a></p>',
                        text, '</section>'])
    preview.append('</html>')
    rendered = '\n'.join(line.rstrip() for line in '\n'.join(preview).splitlines()) + '\n'
    (OUT / 'preview.html').write_text(rendered, encoding='utf-8')
    return manifest


def archive() -> Path:
    validation = json.loads((OUT / 'validation.json').read_text(encoding='utf-8'))
    if validation.get('all_passed') is not True or validation.get('status') != 'passed':
        raise ValueError('A complete successful validation is required before packaging')
    for name, checksum in validation.get('input_sha256', {}).items():
        if digest(safe_path(name).read_bytes()) != checksum:
            raise ValueError(f'Validation input changed after its recorded check: {name}')
    destination = OUT / f'stepik-86957-modern-cpp-{DATE}.zip'
    files = [p for p in OUT.rglob('*') if p.is_file() and p.suffix != '.zip'
             and p.name != 'SHA256SUMS' and '__pycache__' not in p.parts]
    # Include just the reviewed source files and binding metadata, not a full course export.
    manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    files += [ROOT / 'courses/86957/manifest.json']
    files += [ROOT / 'tools/build_modernization_package.py', ROOT / 'tools/verify_modernization.py']
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(files):
            info = zipfile.ZipInfo(str(path.relative_to(ROOT)), date_time=(2026, 11, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, path.read_bytes())
    with zipfile.ZipFile(destination) as z:
        if z.testzip() is not None:
            raise ValueError('Corrupt package')
        manifest = json.loads(z.read('modernization/86957/manifest.json'))
        for step in manifest['steps']:
            for field, checksum in [('target_path', 'after_file_sha256'), ('baseline_path', 'before_file_sha256')]:
                if digest(z.read(step[field])) != step[checksum]:
                    raise ValueError('Archive checksum mismatch')
    (OUT / 'SHA256SUMS').write_text(f'{digest(destination.read_bytes())}  {destination.name}\n', encoding='utf-8')
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', action='store_true', help='Also create ZIP after successful validation')
    args = parser.parse_args()
    manifest = build()
    result = dict(changed_steps=manifest['changed_steps'], changed_lessons=manifest['changed_lessons'])
    if args.archive:
        result['archive'] = str(archive().relative_to(ROOT))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
