#!/usr/bin/env python3
"""Verify the declared editorial coverage and integrity of the LINKS revision.

This checks evidence, hashes, allowed fields and link destinations. Semantic
conclusions are the separate human-readable/editorial reviews, not inferred
from link existence or keyword searches. This tool never accesses Stepik.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

from build_quality_packages import changed_fields, require
from build_theory_upgrade import build

ROOT = Path(__file__).resolve().parents[1]
NAME = 'theory-links-2026-11-23'
PKG = ROOT / 'improvements/86957' / NAME
BASE = '352c2796717a55f4f0db8395b7d6093d8d67c35e'
PART_MODULES = {'foundations': {1, 2, 3}, 'types': {4, 5, 6, 7, 8, 9},
                'ownership': {12, 13, 14, 15},
                'algorithms': {10, 11, 16, 17, 18, 19}}
PUBLISHED_PACKAGES = ['quality-2026-11-23', 'assessment-2026-11-23',
                      'functions-2026-11-23', 'practice-2026-11-23',
                      'theory-2026-11-23', 'theory-continuation-2026-11-23']


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TextLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []
        self.heading = None
        self.headings = []
        self.forbidden = []

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'iframe', 'video'}:
            self.forbidden.append(tag)
        if tag == 'a':
            self.urls.append(dict(attrs).get('href', ''))
        if re.fullmatch(r'h[1-6]', tag):
            self.heading = []

    def handle_endtag(self, tag):
        if re.fullmatch(r'h[1-6]', tag) and self.heading is not None:
            self.headings.append(''.join(self.heading))
            self.heading = None

    def handle_data(self, data):
        if self.heading is not None:
            self.heading.append(data)


def verify():
    manifest = read(PKG / 'manifest.json')
    require(manifest['base_commit'] == BASE, 'Unexpected baseline')
    require(set(manifest['parts']) == set(PART_MODULES), 'Incomplete LINKS parts')
    require(manifest['status'] == 'prepared' and
            manifest['publication']['status'] == 'not_published' and
            manifest['publication']['applied'] is False,
            'This GitHub-only revision must remain unpublished')
    staged, generated = build(manifest['parts'], NAME)
    require(generated == manifest, 'Stale manifest')
    require(all(p.exists() and p.read_bytes() == data for p, data in staged.items()),
            'Stale generated package files')

    # The current user forbids writes to Stepik and to the published snapshot.
    protected = ['courses/86957', 'imports/86957', 'modernization/86957',
                 'corrections/86957'] + ['improvements/86957/' + p
                                       for p in PUBLISHED_PACKAGES]
    altered = subprocess.check_output(['git', 'diff', '--name-only', BASE, '--'] +
                                      protected, cwd=ROOT, text=True).splitlines()
    require(not altered, 'Published/history files changed: ' + ', '.join(altered))
    untracked = subprocess.check_output(
        ['git', 'ls-files', '--others', '--exclude-standard', '--'] + protected,
        cwd=ROOT, text=True).splitlines()
    require(not untracked, 'Unexpected file in protected history/snapshot')

    course = read(ROOT / 'courses/86957/manifest.json')
    bindings = {r['step_id']: r for r in course['step_files']['bindings']}
    bundle = read(ROOT / 'courses/86957/course.json')
    sections = {s['id']: s['position'] for s in bundle['sections']}
    sources = {s['id']: s for s in bundle['step_sources']}
    module = {sid: sections[b['section_ids'][0]] for sid, b in bindings.items()}
    texts = {sid for sid, b in bindings.items() if b['type'] == 'text' and module[sid] <= 19}
    require(len(texts) == 283, 'Unexpected theory inventory')
    changes = {s['step_id']: s for s in manifest['steps']}
    require(set(changes) <= texts, 'Step outside the allowed theory scope')

    reviewed = set()
    reviews = {}
    hashes = {}
    for part, modules in PART_MODULES.items():
        path = PKG / f'review_{part}.json'
        review = read(path)
        expected = {sid for sid in texts if module[sid] in modules}
        ids = review['reviewed_text_step_ids']
        require(len(ids) == len(set(ids)) and set(ids) == expected,
                f'Review coverage mismatch: {part}')
        require(not (reviewed & expected), 'Double-counted editorial coverage')
        require(not review.get('unresolved_defects'), f'Unresolved review: {part}')
        require(set(review['changed_text_step_ids']) ==
                {sid for sid, s in changes.items() if s['part'] == part},
                f'Review/change mismatch: {part}')
        inputs = review['review_inputs']
        require(len(inputs) == len(expected) and
                {r['step_id'] for r in inputs} == expected,
                f'Incomplete reviewed input hashes: {part}')
        for item in inputs:
            source = ROOT / 'courses/86957' / bindings[item['step_id']]['path']
            require(source.relative_to(ROOT).as_posix() == item['source_path'],
                    f'Unexpected review source: {item["step_id"]}')
            doc = read(source)
            require(sha(source) == item['file_sha256'] and
                    hashlib.sha256(doc['block']['text'].encode()).hexdigest() == item['text_sha256'],
                    f'Review source drift: {item["step_id"]}')
            require(doc['block'] == sources[item['step_id']]['block'],
                    f'Snapshot bundle mismatch: {item["step_id"]}')
        reviewed |= expected
        reviews[part] = {'reviewed_texts': len(expected),
                         'changed_texts': len(review['changed_text_step_ids'])}
        hashes[path.relative_to(ROOT).as_posix()] = sha(path)
    require(reviewed == texts, 'Editorial review does not cover all theory modules')

    locations = {(b['lesson_id'], b['position']): sid for sid, b in bindings.items()}
    links = []
    effective = {}
    changed_pre_ids = []
    unchanged_pre_count = 0
    for sid in sorted(texts):
        path = ROOT / (changes[sid]['target_path'] if sid in changes
                       else 'courses/86957/' + bindings[sid]['path'])
        after = read(path)
        effective[sid] = (path, after)
        if sid in changes:
            before = read(ROOT / changes[sid]['baseline_path'])
            require(changed_fields(before, after) == ['block.text'], f'Illegal field change: {sid}')
            old_pre = re.findall(r'<pre\b[^>]*>.*?</pre>', before['block']['text'], re.S)
            new_pre = re.findall(r'<pre\b[^>]*>.*?</pre>', after['block']['text'], re.S)
            if old_pre != new_pre:
                changed_pre_ids.append(sid)
            else:
                unchanged_pre_count += len(old_pre)
        parsed = TextLinks()
        parsed.feed(after['block']['text'])
        require(not parsed.forbidden, f'Active/video element in theory: {sid}')
        require(not any(re.search(r'самопровер|самостоятельн|практикум|упражнени', h, re.I)
                        for h in parsed.headings), f'Unadapted assignment heading: {sid}')
        require(not re.search(r"['\"]\s*\+\s*link\(\d+,\s*\d+,", after['block']['text']),
                f'Unexpanded authoring expression: {sid}')
        for url in parsed.urls:
            u = urlparse(url)
            if u.hostname in {'stepik.org', 'www.stepik.org'}:
                match = re.fullmatch(r'/lesson/(\d+)/step/(\d+)/?', u.path)
                if match:
                    location = tuple(map(int, match.groups()))
                    require(location in locations, f'Unknown internal link: {sid} {url}')
                    links.append({'from_step_id': sid, 'to_step_id': locations[location], 'url': url})
    require(set(changed_pre_ids) == {3212920, 3213209, 3214974},
            'Unexpected change to code/output blocks')

    # Bind editorial acceptance to final texts, not only the source snapshot.
    acceptance = read(PKG / 'review_links.json')
    require(acceptance['status'] == 'accepted_for_github_preparation' and
            not acceptance['unresolved_theory_defects'], 'Unaccepted editorial result')
    final_inputs = acceptance['effective_inputs']
    require(len(final_inputs) == len(texts) and
            {row['step_id'] for row in final_inputs} == texts,
            'Incomplete final editorial input hashes')
    for row in final_inputs:
        path, doc = effective[row['step_id']]
        require(row['path'] == path.relative_to(ROOT).as_posix() and
                row['file_sha256'] == sha(path) and
                row['text_sha256'] == hashlib.sha256(doc['block']['text'].encode()).hexdigest(),
                f'Final editorial acceptance is stale: {row["step_id"]}')
    require(len(acceptance['chains']) == 6 and
            all(c['status'] == 'accepted' and set(c['step_ids']) <= texts
                for c in acceptance['chains']), 'Incomplete semantic chains')
    for row in acceptance['editorial_reports']:
        require(sha(PKG / row['path']) == row['sha256'], 'Stale editorial report reference')
    require({r['path'] for r in acceptance['editorial_reports']} ==
            {f'review_{part}.json' for part in PART_MODULES}, 'Missing editorial report')
    independent_ids = set()
    require({r['path'] for r in acceptance['independent_reports']} ==
            {f'review_{part}_independent.json' for part in PART_MODULES},
            'Missing independent review')
    for row in acceptance['independent_reports']:
        path = PKG / row['path']
        require(sha(path) == row['sha256'], 'Stale independent review reference')
        review = read(path)
        require(review['status'].startswith(('passed', 'accepted')) and
                not review['unresolved_defects'], 'Unresolved independent review')
        targets = review.get('reviewed_target_inputs', review.get('review_inputs', []))
        for target in targets:
            sid = target['step_id']
            require(sid in changes and sid not in independent_ids,
                    'Unexpected or duplicate independent review target')
            actual, doc = effective[sid]
            require(target['target_path'] == actual.relative_to(ROOT).as_posix() and
                    target.get('target_file_sha256', target.get('file_sha256')) == sha(actual) and
                    target.get('target_text_sha256', target.get('text_sha256')) ==
                    hashlib.sha256(doc['block']['text'].encode()).hexdigest(),
                    f'Independent review target drift: {sid}')
            independent_ids.add(sid)
    require(independent_ids == set(changes), 'Incomplete independent review coverage')

    scope_ids = set()
    for name in ['quality-2026-11-23', 'functions-2026-11-23']:
        original = read(ROOT / 'improvements/86957' / name / 'manifest.json')
        scope_ids.update(s['step_id'] for s in original['steps'])
    require(len(scope_ids) == 37 and scope_ids <= reviewed, 'SCOPE unique-ID mismatch')
    scope_review = read(PKG / 'review_scope.json')
    require(len(scope_review['steps']) == len(scope_ids) and
            {s['step_id'] for s in scope_review['steps']} == scope_ids and
            not scope_review['unresolved_assignments'],
            'SCOPE report is incomplete')
    for row in scope_review['steps']:
        path, doc = effective[row['step_id']]
        require(row['effective_path'] == path.relative_to(ROOT).as_posix() and
                row['effective_file_sha256'] == sha(path) and
                row['effective_text_sha256'] == hashlib.sha256(doc['block']['text'].encode()).hexdigest(),
                'Stale SCOPE effective text')

    validations = {}
    for relative in ['validation/ownership.json', 'examples/types/validation.json',
                     'validation/algorithms_current.json']:
        path = PKG / relative
        result = read(path)
        require(result['status'] == 'passed', 'Failed author validation: ' + relative)
        inputs = dict(result.get('input_sha256', {}))
        for row in result.get('step_inputs', []) + result.get('sources', []):
            inputs[row['path']] = row['sha256']
        require(inputs, 'Validation has no source hashes: ' + relative)
        for source, expected_hash in inputs.items():
            require(sha(ROOT / source) == expected_hash, 'Stale validation source: ' + source)
        validations[relative] = {'status': 'passed', 'verified_input_hashes': len(inputs),
                                 'report_sha256': sha(path)}
    hashes.update({str(p.relative_to(ROOT)): sha(p) for p in PKG.rglob('*')
                   if p.is_file() and p.suffix in {'.json', '.py', '.cpp', '.inc', '.step'}
                   and '/validation/' not in p.as_posix()
                   and p.name != 'validation.json'})
    hashes.update({str(p.relative_to(ROOT)): sha(p) for p in
                   [Path(__file__).resolve(), ROOT / 'tools/build_theory_upgrade.py',
                    ROOT / 'tools/render_course_tree.py']})
    return {'schema_version': 1, 'status': 'passed', 'base_commit': BASE,
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'scope': 'Current GitHub-only LINKS revision; source and evidence integrity, not proof of every program',
            'reviewed_theory_text_steps': len(reviewed), 'modules': list(range(1, 20)),
            'changed_steps': len(changes), 'changed_lessons': manifest['changed_lessons'],
            'independently_reviewed_changed_steps': len(independent_ids),
            'accepted_semantic_chains': len(acceptance['chains']),
            'review_parts': reviews, 'scope_original_text_ids': sorted(scope_ids),
            'scope_unique_steps': len(scope_ids),
            'checked_internal_link_occurrences': len(links),
            'changed_pre_step_ids': sorted(changed_pre_ids),
            'byte_identical_pre_blocks_in_other_changed_steps': unchanged_pre_count,
            'all_step_changes_only_block_text': True,
            'published_snapshot_and_historical_packages_unchanged': True,
            'new_practice': False, 'new_video': False,
            'runtime_validation_reports': validations, 'input_sha256': hashes,
            'live_stepik_access': False, 'publication': manifest['publication'],
            'limitations': ['Link existence is structural; meaning is assessed in the four editorial reviews.',
                            'Current runtime checks are limited to the named examples and claims.',
                            'No new Windows/MSVC, macOS, historical CMake/GoogleTest or graded-task run.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, help='Save this run separately from historical reports')
    args = parser.parse_args()
    report = verify()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['status', 'reviewed_theory_text_steps',
        'changed_steps', 'changed_lessons', 'scope_unique_steps', 'checked_internal_link_occurrences']},
        ensure_ascii=False))


if __name__ == '__main__':
    main()
