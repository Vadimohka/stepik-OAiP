#!/usr/bin/env python3
"""Check the cumulative GitHub-only theory revision and its current evidence.

Semantic acceptance comes from the named full-reading and independent reviews.
This gate verifies their coverage, exact inputs, allowed edits and current tests;
it does not infer correctness from a heading or a passing compiler invocation.
No network access or Stepik operations are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse

from build_quality_packages import changed_fields, require
from build_theory_upgrade import build
from verify_theory_links import TextLinks

ROOT = Path(__file__).resolve().parents[1]
NAME = 'theory-final-review-2026-11-23'
PKG = ROOT / 'improvements/86957' / NAME
BASE = '26bbfeb5065ef3475f9ea612a3a8785f934b7c49'
PARTS = {'foundations': set(range(1, 5)), 'core': set(range(5, 12)),
         'advanced': set(range(12, 20))}


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(doc):
    return hashlib.sha256(doc['block']['text'].encode()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def require_hashes(items):
    for path, expected in items.items():
        require((ROOT / path).is_file() and sha(ROOT / path) == expected,
                'Stale input: ' + path)


def review_rows(part, review):
    if part == 'foundations':
        return [(r['step_id'], r['effective_path'], r['file_sha256'], r['text_sha256'],
                 r['result_path'], r['result_file_sha256'], r['result_text_sha256'])
                for r in review['review_inputs']]
    if part == 'core':
        require(all(r['read_complete'] for r in review['reviewed_steps']), 'Incomplete core reading')
        return [(r['step_id'], r['previous_effective_path'], r['previous_file_sha256'],
                 r['previous_text_sha256'], r['reviewed_final_path'],
                 r['reviewed_final_file_sha256'], r['reviewed_final_text_sha256'])
                for r in review['reviewed_steps']]
    require(all(r['reviewed_entire_text'] for r in review['steps']), 'Incomplete advanced reading')
    return [(r['step_id'], r['source_path'], r['source_file_sha256'], r['source_text_sha256'],
             r['result_path'], r['result_file_sha256'], r['result_text_sha256'])
            for r in review['steps']]


def verify():
    manifest = read(PKG / 'manifest.json')
    require(manifest['base_commit'] == BASE, 'Unexpected package base')
    require(manifest['status'] == 'prepared' and
            manifest['publication']['status'] == 'not_published' and
            manifest['publication']['applied'] is False, 'GitHub-only publication boundary')
    staged, generated = build(manifest['parts'], NAME)
    require(generated == manifest and all(p.is_file() and p.read_bytes() == b for p, b in staged.items()),
            'Stale generated package')

    # Everything outside this package, the active plan and three declared tools
    # must remain byte-identical to the starting commit, including old receipts.
    allowed_prefixes = [rel(PKG) + '/', 'improvements/86957/theory-review-2026-11-23/']
    allowed_files = {'tools/build_theory_upgrade.py', 'tools/render_course_tree.py',
                     'tools/verify_theory_final.py'}
    modified = subprocess.check_output(['git', 'diff', '--name-only', BASE, '--'],
                                       cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'],
                                        cwd=ROOT, text=True).splitlines()
    require(all(p in allowed_files or any(p.startswith(prefix) for prefix in allowed_prefixes)
                for p in modified + untracked), 'Out-of-scope repository modification')
    active_allowed = {'README.md', 'PROGRESS.md', 'backlog.json', 'scope.json', 'module_review.json'}
    require(all(Path(p).name in active_allowed for p in modified + untracked
                if p.startswith(allowed_prefixes[1])), 'Unexpected active-plan file')

    source_index = read(PKG / 'review_inputs.json')
    require(source_index['base_commit'] == BASE, 'Wrong editorial input base')
    inputs = {r['step_id']: r for r in source_index['steps']}
    require(len(inputs) == len(source_index['steps']) == 283, 'Incomplete source inventory')
    course = read(ROOT / 'courses/86957/manifest.json')
    bindings = {r['step_id']: r for r in course['step_files']['bindings']}
    bundle = read(ROOT / 'courses/86957/course.json')
    sections = {s['id']: s['position'] for s in bundle['sections']}
    eligible = {sid for sid, b in bindings.items()
                if b['type'] == 'text' and sections[b['section_ids'][0]] <= 19}
    require(set(inputs) == eligible, 'Wrong theory scope')
    changes = {r['step_id']: r for r in manifest['steps']}
    new = {sid for sid, r in changes.items() if r['revision_role'] == 'new_correction'}
    carried = set(changes) - new
    old_manifest = read(ROOT / 'improvements/86957/theory-links-2026-11-23/manifest.json')
    old_changes = {r['step_id']: r for r in old_manifest['steps']}
    require(len(new) == 6 and len(carried) == 49 and len(changes) == 55, 'Wrong cumulative membership')
    require(set(old_changes) | new == set(changes) and len(set(old_changes) & new) == 1,
            'Lost or duplicated pending changes')
    effective, unchanged_pre = {}, 0
    for sid, row in inputs.items():
        source = ROOT / row['effective_path']
        pinned = subprocess.check_output(['git', 'show', BASE + ':' + row['effective_path']], cwd=ROOT)
        require(source.read_bytes() == pinned and sha(source) == row['file_sha256'] and
                text_sha(read(source)) == row['text_sha256'], f'Editorial source drift: {sid}')
        path = ROOT / changes[sid]['target_path'] if sid in changes else source
        doc = read(path)
        effective[sid] = (path, doc)
        if sid in new:
            previous = read(source)
            require(changed_fields(previous, doc) == ['block.text'], f'Illegal correction: {sid}')
            previous_pre = re.findall(r'<pre\b[^>]*>.*?</pre>', previous['block']['text'], re.S)
            require(previous_pre == re.findall(r'<pre\b[^>]*>.*?</pre>', doc['block']['text'], re.S),
                    f'Unexpected lesson code edit: {sid}')
            unchanged_pre += len(previous_pre)
        elif sid in carried:
            require(path.read_bytes() == (ROOT / old_changes[sid]['target_path']).read_bytes(),
                    f'Carried lesson changed: {sid}')

    reviews, reviewed, independently_reviewed = {}, set(), set()
    evidence_hashes = {}
    for part, modules in PARTS.items():
        expected = {sid for sid, r in inputs.items() if r['module_number'] in modules}
        path = PKG / f'review_{part}.json'
        review = read(path)
        require(not review['unresolved_defects'], 'Unresolved author review: ' + part)
        rows = review_rows(part, review)
        require(len(rows) == len(expected) and {r[0] for r in rows} == expected,
                'Incomplete full reading: ' + part)
        expected_changes = {sid for sid in new if changes[sid]['part'] == part}
        require(set(review['changed_text_step_ids']) == expected_changes, 'Wrong reviewed changes')
        for sid, previous_path, previous_sha, previous_text, final_path, final_sha, final_text in rows:
            source = inputs[sid]
            require((previous_path, previous_sha, previous_text) ==
                    (source['effective_path'], source['file_sha256'], source['text_sha256']),
                    f'Wrong reviewed source: {sid}')
            actual, doc = effective[sid]
            # Carried files acquire a new package path but preserve identical bytes.
            expected_path = rel(actual) if sid in new else source['effective_path']
            require(final_path == expected_path and final_sha == sha(actual) and final_text == text_sha(doc),
                    f'Stale reviewed result: {sid}')
        require(not reviewed & expected, 'Duplicate review coverage')
        reviewed |= expected
        evidence_hashes[rel(path)] = sha(path)
        independent_path = PKG / f'review_{part}_independent.json'
        independent = read(independent_path)
        require(independent['status'] == 'passed' and not independent['unresolved_defects'],
                'Independent review not accepted: ' + part)
        require(set(independent['reviewed_changed_step_ids']) == expected_changes,
                'Wrong independent review scope')
        require(len(independent['target_inputs']) == len(expected_changes), 'Missing independent hashes')
        for item in independent['target_inputs']:
            sid = item['step_id']
            require(sid in expected_changes and sid not in independently_reviewed, 'Duplicate review target')
            actual, doc = effective[sid]
            require(item['path'] == rel(actual) and item['file_sha256'] == sha(actual) and
                    item['text_sha256'] == text_sha(doc), 'Independent target drift')
            independently_reviewed.add(sid)
        supporting = dict(independent.get('test_inputs_sha256', {}))
        for row in independent.get('supporting_inputs', []) + independent.get('reviewed_testinputs', []):
            supporting[row['path']] = row['sha256']
        require_hashes(supporting)
        evidence_hashes[rel(independent_path)] = sha(independent_path)
        reviews[part] = {'fully_read_texts': len(expected), 'independently_accepted_corrections': len(expected_changes)}
    require(reviewed == eligible and independently_reviewed == new, 'Incomplete acceptance coverage')

    acceptance = read(PKG / 'review_completion.json')
    require(acceptance['status'] == 'accepted_for_github_preparation' and
            not acceptance['unresolved_theory_defects'], 'Unaccepted result')
    final_inputs = acceptance['effective_inputs']
    require(len(final_inputs) == 283 and {r['step_id'] for r in final_inputs} == eligible,
            'Incomplete final acceptance')
    for row in final_inputs:
        path, doc = effective[row['step_id']]
        require(row['path'] == rel(path) and row['file_sha256'] == sha(path) and
                row['text_sha256'] == text_sha(doc), 'Final acceptance hash mismatch')
    require_hashes(acceptance['review_evidence_sha256'])
    integration_path = PKG / 'review_integration_independent.json'
    integration = read(integration_path)
    require(integration['status'] == 'passed' and not integration['unresolved_defects'],
            'Independent integration review is incomplete')
    require_hashes(integration['input_sha256'])
    evidence_hashes[rel(integration_path)] = sha(integration_path)
    scope_ids = set()
    for name in ['quality-2026-11-23', 'functions-2026-11-23']:
        scope_ids |= {s['step_id'] for s in read(ROOT / 'improvements/86957' / name / 'manifest.json')['steps']}
    require(len(scope_ids) == 37 and {s['step_id'] for s in acceptance['scope_steps']} == scope_ids,
            'Incorrect SCOPE inventory')
    for row in acceptance['scope_steps']:
        path, doc = effective[row['step_id']]
        require(row['path'] == rel(path) and row['file_sha256'] == sha(path) and
                row['text_sha256'] == text_sha(doc) and row['new_adaptation'] is False,
                'Stale SCOPE or double-counted adaptation')
    previous_scope_path = ROOT / 'improvements/86957/theory-links-2026-11-23/review_scope.json'
    require(acceptance['previous_scope_acceptance_sha256'] == sha(previous_scope_path),
            'Previous SCOPE evidence drift')
    previous_scope = {s['step_id']: s for s in read(previous_scope_path)['steps']}
    require(all(row['file_sha256'] == previous_scope[row['step_id']]['effective_file_sha256']
                for row in acceptance['scope_steps']), 'Unexpected new SCOPE adaptation')

    backlog = read(ROOT / 'improvements/86957/theory-review-2026-11-23/backlog.json')
    expected_manifest = '../theory-final-review-2026-11-23/manifest.json'
    require(backlog['execution_base_commit'] == BASE and backlog['current_manifest'] == expected_manifest,
            'Active plan points to a superseded revision')
    package_states = {p['id']: p['execution'] for p in backlog['packages']}
    require(package_states['VERIFY']['status'] == 'completed_and_independently_verified' and
            package_states['PUB']['status'] == 'pending_cumulative_publication_blocked_by_owner_instruction' and
            package_states['PUB']['manifest'] == expected_manifest and
            package_states['PUB']['next_action_if_authorized'] == package_states['PUB']['next_action'],
            'Stale active verification/publication state')

    locations = {(b['lesson_id'], b['position']): sid for sid, b in bindings.items()}
    internal_links = 0
    for sid, (_, doc) in effective.items():
        parser = TextLinks(); parser.feed(doc['block']['text'])
        require(not parser.forbidden, f'Active/video element: {sid}')
        require(not any(re.search(r'самопровер|самостоятельн|практикум|упражнени', h, re.I)
                        for h in parser.headings), f'Unadapted assignment heading: {sid}')
        for url in parser.urls:
            parsed = urlparse(url)
            if parsed.hostname in {'stepik.org', 'www.stepik.org'}:
                match = re.fullmatch(r'/lesson/(\d+)/step/(\d+)/?', parsed.path)
                if match:
                    require(tuple(map(int, match.groups())) in locations, f'Unknown link: {sid} {url}')
                    internal_links += 1

    runtime = read(PKG / 'runtime_summary.json')
    require(runtime['status'] == 'passed', 'Runtime summary not accepted')
    require(len(runtime['per_suite']) == 14 and
            len({s['suite'] for s in runtime['per_suite']}) == 14, 'Duplicate runtime suites')
    require_hashes({r['path']: r['sha256'] for r in runtime['source_reports']})
    for suite in runtime['per_suite']:
        require(suite['status'] == 'passed', 'Unaccepted numeric suite')
        require_hashes({suite['report_path']: suite['report_sha256'],
                        suite['verifier_path']: suite['verifier_sha256']})
    require(all(sum(s['normalized_counts'][key] for s in runtime['per_suite']) == total
                for key, total in runtime['totals'].items()), 'Incorrect runtime aggregate')
    # Per-suite input hashes are verified independently of the aggregate counts.
    recheck = read(PKG / 'validation/recheck/summary.json')
    require(recheck['status'] == 'passed' and len(recheck['suites']) == 11 and
            recheck['runner_sha256'] == sha(PKG / 'recheck_examples.py'), 'Stale historical rerun')
    validations = {}
    for suite in recheck['suites']:
        path = PKG / 'validation/recheck' / (suite['name'] + '.json')
        result = read(path)
        require(suite['status'] == result['status'] == 'passed' and suite['exit_code'] == 0 and
                suite['report_sha256'] == sha(path) and
                suite['verifier_sha256'] == sha(ROOT / suite['verifier_path']), 'Stale suite record')
        source_hashes = dict(result.get('input_sha256', {}))
        for row in result.get('step_inputs', []) + result.get('sources', []):
            source_hashes[row['path']] = row['sha256']
        require(source_hashes, 'Missing suite input hashes')
        resolved = {}
        for source, expected in source_hashes.items():
            actual = ROOT / source
            if not actual.exists(): actual = ROOT / suite['source_package'] / source
            resolved[rel(actual)] = expected
        require_hashes(resolved)
        validations[suite['name']] = {'report': rel(path), 'sha256': sha(path),
                                      'verified_input_hashes': len(resolved)}
    for part in PARTS:
        path = PKG / 'validation' / f'new_{part}.json'
        result = read(path)
        require(result['status'] == 'passed', 'Failed new author suite')
        require_hashes(result['input_sha256'])
        validations['new_' + part] = {'report': rel(path), 'sha256': sha(path),
                                      'verified_input_hashes': len(result['input_sha256'])}
    completed = subprocess.run([sys.executable, str(PKG / 'verify_code_coverage.py'), '--check'],
                               cwd=ROOT, text=True, capture_output=True)
    require(completed.returncode == 0, 'Code coverage gate: ' + completed.stdout + completed.stderr)
    evidence_hashes.update({rel(PKG / name): sha(PKG / name) for name in
                           ['review_inputs.json', 'review_completion.json', 'manifest.json',
                            'runtime_summary.json', 'code_coverage.json', 'verify_code_coverage.py']})
    evidence_hashes.update({rel(ROOT / name): sha(ROOT / name) for name in
                           ['tools/verify_theory_final.py', 'tools/build_theory_upgrade.py',
                            'tools/render_course_tree.py']})
    return {'schema_version': 1, 'status': 'passed', 'base_commit': BASE,
            'scope': 'Complete declared text review and exact evidence integrity; not formal program verification.',
            'reviewed_theory_text_steps': 283, 'modules': list(range(1, 20)),
            'review_parts': reviews, 'new_corrections': len(new), 'carried_forward': len(carried),
            'cumulative_pending_text_steps': len(changes), 'cumulative_lessons': manifest['changed_lessons'],
            'new_correction_step_ids': sorted(new), 'all_step_changes_only_block_text': True,
            'new_lesson_pre_edits': 0, 'preserved_pre_in_six_corrected_texts': unchanged_pre,
            'scope_original_text_ids': sorted(scope_ids), 'new_scope_adaptations': 0,
            'checked_internal_link_occurrences': internal_links,
            'published_snapshot_and_historical_packages_unchanged': True,
            'runtime_reports': validations, 'input_sha256': evidence_hashes,
            'new_practice': False, 'new_video': False, 'live_stepik_access': False,
            'publication': manifest['publication'],
            'limitations': ['All standalone positive listings are bound to current source checks; snippets and commands are separately classified.',
                            'Finite examples and traces do not prove all inputs, allocation failures or template instantiations.',
                            'Current execution is Linux/GCC C++17/C++20; no new Windows/MSVC, macOS or graded checker run.',
                            'No live Stepik content, placement or HTML rendering was inspected.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = verify()
    path = PKG / 'validation/integrity.json'
    if args.check:
        require(path.is_file() and read(path) == result, 'Saved integrity result is stale')
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'reviewed_theory_text_steps',
                     'new_corrections', 'carried_forward', 'cumulative_pending_text_steps',
                     'checked_internal_link_occurrences']}))


if __name__ == '__main__':
    main()
