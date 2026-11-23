#!/usr/bin/env python3
"""Build the theory-only revision; immutable baselines, no network writes.

--parts allows complete editorial blocks to be committed while others are being
written. --check always checks the exact parts listed in the saved manifest.
"""
from __future__ import annotations
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse

from build_quality_packages import (block_digest, changed_fields, digest,
                                    json_bytes, load_bindings, require)
from build_next_upgrade import render_preview

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / 'improvements/86957/theory-2026-11-23'
BASE_COMMIT = '07f9f91852c2dbe5e6a9cdab6ccd90230cd2eb79'
TITLE = 'Теория C++: точность, современность и связанность'
PACKAGE_CONFIGS = {
    'theory-2026-11-23': (BASE_COMMIT, TITLE),
    'theory-continuation-2026-11-23': (
        'd96e5b9cffa65010c53894a9b65b1a497cb6b58a',
        'Продолжение теоретической редакции C++: типы, классы и сквозные связи'),
    'theory-links-2026-11-23': (
        '352c2796717a55f4f0db8395b7d6093d8d67c35e',
        'Сквозное согласование теории C++: предпосылки, термины и переходы'),
    'theory-final-review-2026-11-23': (
        '26bbfeb5065ef3475f9ea612a3a8785f934b7c49',
        'Независимая проверка всей теории C++ и итоговая подготовленная редакция'),
}


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []
        self.headings = []
        self.heading = None
        self.errors = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'script', 'iframe', 'video'}:
            self.errors.append('Active or video element: ' + tag)
        if tag == 'a' and attrs.get('href'):
            self.urls.append(attrs['href'])
        if re.fullmatch('h[1-6]', tag): self.heading = []
    def handle_endtag(self, tag):
        if re.fullmatch('h[1-6]', tag) and self.heading is not None:
            self.headings.append(''.join(self.heading))
            self.heading = None
    def handle_data(self, data):
        if self.heading is not None: self.heading.append(data)


def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def change_table(steps):
    lines = ['| Шаг | Урок / позиция | Блок | Изменение |', '| --- | --- | --- | --- |']
    for step in steps:
        summary = step['summary'].replace('|', '\\|').replace('\n', ' ')
        lines.append(f'| [{step["step_id"]}]({step["step_url"]}) | '
                     f'{step["lesson_id"]} / {step["position"]} | {step["part"].upper()} | {summary} |')
    return lines


def changes_by_module(steps, bindings):
    grouped = {}
    for step in steps:
        section_ids = bindings[step['step_id']]['section_ids']
        require(section_ids, f'Step has no course module: {step["step_id"]}')
        grouped.setdefault(section_ids[0], []).append(step)

    modules = []
    for section_id, rows in grouped.items():
        path = ROOT / 'courses/86957/raw/sections' / f'{section_id}.json'
        section = json.loads(path.read_bytes())
        title = html.escape(' '.join(section['title'].split())).replace('[', '\\[').replace(']', '\\]')
        modules.append((section['position'], title, rows))
    modules.sort(key=lambda module: module[0])

    lines = ['## Оглавление по модулям', '']
    for number, title, rows in modules:
        lines.append(f'- [Модуль {number}. {title} ({len(rows)})](#module-{number})')
    for number, title, rows in modules:
        lines.extend(['', f'<a name="module-{number}"></a>', '', f'## Модуль {number}. {title}', ''])
        lines.extend(change_table(rows))
    return lines


def build(parts=None, package='theory-2026-11-23'):
    PKG = ROOT / 'improvements/86957' / package
    BASE_COMMIT, TITLE = PACKAGE_CONFIGS[package]
    bindings, order = load_bindings(ROOT)
    locations = {(b['lesson_id'], b['position']): int(sid) for sid,b in bindings.items()}
    index = json.loads((PKG/'base_source_index.json').read_bytes())
    require(index['base_commit'] == BASE_COMMIT and len(index['files']) == 485,
            'Wrong baseline source index')
    # Verify the index itself against Git, not only against its own recorded hashes.
    pinned_tree = subprocess.check_output(
        ['git', 'rev-parse', BASE_COMMIT + '^{tree}'], cwd=ROOT, text=True).strip()
    pinned_files = {}
    for line in subprocess.check_output(
            ['git', 'ls-tree', '-r', BASE_COMMIT, '--', 'courses/86957/steps'],
            cwd=ROOT, text=True).splitlines():
        metadata, path = line.split('\t', 1)
        if path.endswith('.step'):
            pinned_files[path] = metadata.split()[2]
    require(index['tree_sha'] == pinned_tree and index['files'] == pinned_files,
            'Source index differs from the pinned Git commit')
    previous_path = PKG/'manifest.json'
    previous = json.loads(previous_path.read_bytes()) if previous_path.exists() else None
    old = {s['step_id']: s for s in previous['steps']} if previous else {}
    if previous:
        require(previous['base_commit'] == BASE_COMMIT, 'Unexpected previous baseline')
    journals = sorted(PKG.glob('changes_*.json'))
    selected = sorted(parts or [p.stem.removeprefix('changes_') for p in journals])
    require(bool(selected) and len(selected) == len(set(selected)), 'Empty/duplicate parts')
    changes = {}
    for part in selected:
        named_parts = {
            'theory-links-2026-11-23': {'foundations', 'types', 'ownership', 'algorithms'},
            'theory-final-review-2026-11-23': {'carried', 'foundations', 'core', 'advanced'},
        }
        valid_part = (part in named_parts[package] if package in named_parts
                      else re.fullmatch(r't[1-6]b?', part))
        require(valid_part, 'Invalid editorial part')
        path = PKG/f'changes_{part}.json'
        rows = json.loads(path.read_bytes())
        if isinstance(rows, dict): rows = rows['changes']
        for row in rows:
            sid = int(row['step_id'])
            require(sid not in changes, f'Duplicate journal ID {sid}')
            require(isinstance(row.get('summary'),str) and row['summary'].strip(),f'No summary {sid}')
            require(row.get('sources') and all(url.startswith('https://') for url in row['sources']),f'No primary source {sid}')
            changes[sid] = dict(row, part=part)
    staged, documents, steps, links = {}, {}, [], []
    for sid in sorted(changes, key=lambda sid: order[sid]):
        row, binding = changes[sid], bindings[sid]
        relative = Path(row['path'])
        require(relative.as_posix() == binding['path'] and binding['type'] == 'text',f'Wrong binding/type {sid}')
        require(re.fullmatch(r'steps/\d+/\d+_\d+_text\.step',relative.as_posix()),f'Unsafe path {sid}')
        source = ROOT/'courses/86957'/relative
        baseline = PKG/'baseline'/relative
        target = PKG/relative
        require(not target.is_symlink() and not baseline.is_symlink(),f'Symlink {sid}')
        before_bytes = baseline.read_bytes() if baseline.exists() else source.read_bytes()
        source_name = source.relative_to(ROOT).as_posix()
        require(blob_sha(before_bytes) == index['files'][source_name],f'Baseline differs from pinned GitHub tree: {sid}')
        if not baseline.exists(): staged[baseline] = before_bytes
        after_bytes = target.read_bytes()
        before, after = json.loads(before_bytes), json.loads(after_bytes)
        require(str(before['id']) == str(after['id']) == str(sid),f'Payload ID mismatch {sid}')
        fields = changed_fields(before,after)
        require(fields == ['block.text'],f'Out-of-scope or empty edit {sid}: {fields}')
        require(after['block']['name'] == 'text',f'Non-theory step {sid}')
        if package != 'theory-2026-11-23':
            require(not re.search(r"['\"]\s*\+\s*link\(\d+,\s*\d+,", after['block']['text']),
                    f'Unexpanded link generator in explanation: {sid}')
        parser = Links(); parser.feed(after['block']['text'])
        require(not parser.errors, f'{sid}: {parser.errors}')
        require(parser.headings, f'Missing explanation heading {sid}')
        require(not any(re.search(r'самопровер|самостоятельн|практикум|упражнени',h,re.I) for h in parser.headings),f'Learner assignment heading {sid}')
        for url in parser.urls:
            u = urlparse(url)
            if u.hostname in {'stepik.org','www.stepik.org'}:
                match = re.fullmatch(r'/lesson/(\d+)/step/(\d+)/?',u.path)
                if match:
                    location=tuple(map(int,match.groups()))
                    require(location in locations,f'Invalid course link {sid}: {url}')
                    links.append({'from_step_id':sid,'to_step_id':locations[location],'url':url})
        record = dict(step_id=sid, lesson_id=binding['lesson_id'],position=binding['position'],
                      source_path=source_name,target_path=target.relative_to(ROOT).as_posix(),
                      baseline_path=baseline.relative_to(ROOT).as_posix(),
                      before_file_sha256=digest(before_bytes),after_file_sha256=digest(after_bytes),
                      before_block_sha256=block_digest(before['block']),after_block_sha256=block_digest(after['block']),
                      changed_fields=fields,summary=row['summary'],sources=row['sources'],
                      plan=row.get('plan',[row['part'].upper(),'LINKS']),part=row['part'],step_url=binding['step_url'])
        if package == 'theory-final-review-2026-11-23':
            effective_index = json.loads((PKG/'review_inputs.json').read_bytes())
            require(effective_index['base_commit'] == BASE_COMMIT, 'Wrong effective baseline')
            entry = next(x for x in effective_index['steps'] if x['step_id'] == sid)
            effective_bytes = subprocess.check_output(
                ['git', 'show', BASE_COMMIT + ':' + entry['effective_path']], cwd=ROOT)
            require(digest(effective_bytes) == entry['file_sha256'], 'Effective baseline hash mismatch')
            effective_before = json.loads(effective_bytes)
            amended = effective_before['block']['text'] != after['block']['text']
            require((row['part'] == 'carried') != amended, 'Incorrect carry/correction classification')
            record.update(previous_effective_path=entry['effective_path'],
                          previous_effective_file_sha256=entry['file_sha256'],
                          revision_role='new_correction' if amended else 'carried_forward')
        if sid in old:
            require(old[sid]['before_file_sha256']==record['before_file_sha256'],f'Mutated immutable baseline {sid}')
            if previous['publication'].get('applied'):
                require(old[sid]['after_file_sha256']==record['after_file_sha256'],f'Published revision edited {sid}')
        documents[sid]=after;steps.append(record)
    if previous and previous['publication'].get('applied'):
        require(set(old)==set(changes),'Published package membership changed')
    publication = previous['publication'] if previous else {
        'status':'not_published','applied':False,
        'note':('Только GitHub по прямому указанию владельца от 23 ноября 2026 года; '
                'изменения на Stepik в этой сессии не разрешены.'
                if package in {'theory-links-2026-11-23', 'theory-final-review-2026-11-23'} else
                'Новая редакция только теории; публикация проверяется отдельно.')}
    manifest = {'schema_version':1,'course_id':86957,'date':'2026-11-23','base_commit':BASE_COMMIT,
                'status':'published' if publication.get('status')=='verified_on_stepik' else 'prepared',
                'parts':selected,'changed_steps':len(steps),'changed_lessons':len({s['lesson_id'] for s in steps}),
                'publication':publication,'scope':{'allowed_fields':['block.text'],'allowed_step_types':['text'],
                'new_practice':False,'new_video':False,'existing_assessment_changes':False},'steps':steps}
    if package == 'theory-final-review-2026-11-23':
        predecessor = ROOT/'improvements/86957/theory-links-2026-11-23/manifest.json'
        predecessor_ids = {x['step_id'] for x in json.loads(predecessor.read_bytes())['steps']}
        require(predecessor_ids <= set(changes), 'Pending LINKS edits lost from cumulative revision')
        manifest['preparation'] = {
            'kind': 'cumulative_pending_theory_revision',
            'supersedes_prepared_manifest': predecessor.relative_to(ROOT).as_posix(),
            'previous_package_files_preserved': True,
            'new_correction_step_ids': [s['step_id'] for s in steps if s['revision_role'] == 'new_correction'],
            'carried_forward_step_ids': [s['step_id'] for s in steps if s['revision_role'] == 'carried_forward'],
            'note': 'Для будущего PUB используется этот единый пакет; прежний LINKS не переносится отдельно повторно.'}
    staged[PKG/'manifest.json']=json_bytes(manifest)
    staged[PKG/'course_links.json']=json_bytes({'schema_version':1,'links':links,'checked_against':'courses/86957/manifest.json'})
    preview = render_preview(PKG,manifest,TITLE,documents)
    if package != 'theory-2026-11-23':
        # Preview-only whitespace hygiene; canonical .step code is unchanged.
        preview = ('\n'.join(line.rstrip(' \t') for line in
                             preview.decode('utf-8').split('\n'))).encode('utf-8')
    staged[PKG/'preview.html']=preview
    grouped_journal = package in {'theory-continuation-2026-11-23', 'theory-links-2026-11-23',
                                 'theory-final-review-2026-11-23'}
    lesson_count = manifest['changed_lessons']
    size_line = (f'**Шаги** — {len(steps)} · **Уроки** — {lesson_count}.' if grouped_journal
                 else f'Изменено **{len(steps)} текстовых шагов в {lesson_count} уроках**.')
    lines=[f'# {TITLE}','','Базовый коммит: `'+BASE_COMMIT+'`.','',
           size_line,
           'Меняется исключительно `block.text`; ID, типы, позиции и задания сохранены.','',
           f'Статус публикации: `{publication["status"]}`.','',
           '[Превью](preview.html) · [Манифест](manifest.json) · [Связи между шагами](course_links.json)','']
    if grouped_journal:
        lines.extend(changes_by_module(steps, bindings))
    else:
        lines.extend(change_table(steps))
    lines += ['','## Проверка','','`python3 tools/build_theory_upgrade.py --check` проверяет точные исходные байты по дереву закреплённого коммита, единственное изменяемое поле, привязки шагов, внутренние ссылки и воспроизводимость манифеста/превью.','',
              'Компиляция и прогоны — авторская проверка разобранных примеров, а не новые задания учащимся. Исторические пакеты не переписываются.','']
    staged[PKG/'CHANGES.md']='\n'.join(lines).encode()
    return staged,manifest


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--check',action='store_true')
    ap.add_argument('--parts',nargs='+')
    ap.add_argument('--package', choices=PACKAGE_CONFIGS,
                    help='One package; default: all registered theory packages')
    args=ap.parse_args()
    try:
        require(not args.parts or args.package, '--parts requires an explicit --package')
        packages = [args.package] if args.package else list(PACKAGE_CONFIGS)
        for package in packages:
            parts=args.parts
            if args.check:
                require(parts is None,'--check uses saved manifest parts')
                parts=json.loads((ROOT/'improvements/86957'/package/'manifest.json').read_bytes())['parts']
            staged,manifest=build(parts, package)
            mismatches=[p for p,data in staged.items() if not p.exists() or p.read_bytes()!=data]
            if args.check:
                require(not mismatches,'Stale generated files: '+', '.join(p.relative_to(ROOT).as_posix() for p in mismatches))
            else:
                for path in mismatches:
                    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(staged[path])
            print(json.dumps({'package':package,'status':'checked' if args.check else 'built','steps':manifest['changed_steps'],'lessons':manifest['changed_lessons'],'parts':manifest['parts'],'written':0 if args.check else len(mismatches)}))
        return 0
    except Exception as error:
        print(f'{type(error).__name__}: {error}',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
