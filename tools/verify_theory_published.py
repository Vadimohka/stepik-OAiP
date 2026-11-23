#!/usr/bin/env python3
"""Verify the published theory snapshot using saved Git/API evidence only.

The five preparation gates keep their original meaning and run unchanged in a
disposable detached worktree at PREPARED. Current publication, placement, source
and learner projections, and exact lesson text/code are checked separately.
There is no network access, Stepik operation or new compiler test run here.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

from build_quality_packages import changed_fields, require
from verify_theory_links import TextLinks

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'improvements/86957/theory-final-review-2026-11-23'
PKG = ROOT / PACKAGE
PREPARED = '5b3946ed7864ff22231bdbd16a4485ced71e6592'
PUBLISHED = 'cd85f40b17f4cfd4992e94e5def8d6ff0374b7b7'
RECEIPT = 'courses/86957/publication-verification-theory-final-review-2026-11-23.json'
REPORT = PKG / 'publication_closeout/verification.json'
REL_ATTRIBUTE = ' rel="noopener noreferrer nofollow"'
SOURCE_BLOCK_ONLY = {'feedback_correct', 'feedback_wrong', 'source', 'subtitles', 'tests_archive'}
SOURCE_ONLY = {'reason_of_failure', 'error', 'warnings', 'cost'}
PREPARATION_CHECKS = [
    ['tools/build_theory_upgrade.py', '--check'],
    ['tools/verify_theory_final.py', '--check'],
    [PACKAGE + '/verify_code_coverage.py', '--check'],
    [PACKAGE + '/verify_preserved_whitespace.py', '--check'],
    ['tools/render_course_tree.py', '--check'],
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def pinned(commit, path):
    return git('show', commit + ':' + path)


def tree_files(commit, prefix):
    result = {}
    for row in git('ls-tree', '-rz', commit, '--', prefix).split(b'\0'):
        if not row:
            continue
        metadata, path = row.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        require(kind == 'blob' and mode in {'100644', '100755'}, 'Unexpected tree entry')
        result[path.decode()] = oid
    return result


def verify_tree_files(commit, prefix, exceptions=()):
    """Verify working files against pinned blobs, without trusting the index."""
    verified = {}
    for path, oid in tree_files(commit, prefix).items():
        if path in exceptions:
            continue
        actual = ROOT / path
        require(actual.is_file() and not actual.is_symlink(), 'Missing/symlink source: ' + path)
        data = actual.read_bytes()
        git_sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(git_sha == oid, 'Pinned source changed: ' + path)
        verified[path] = sha(data)
    return verified


def add_missing_anchor_rel(text):
    """The sole observed HTML transformation; no whitespace/DOM normalization."""
    count = 0

    def replace(match):
        nonlocal count
        tag = match.group(0)
        if re.search(r'\brel\s*=', tag):
            return tag
        require(re.search(r'\bhref\s*=', tag), 'Unsupported anchor without href')
        count += 1
        return tag[:-1] + REL_ATTRIBUTE + '>'

    return re.sub(r'<a\b[^>]*>', replace, text), count


def run_preparation_checks():
    results = []
    with tempfile.TemporaryDirectory(prefix='theory-prepared-', dir=ROOT.parent) as directory:
        path = Path(directory) / 'checkout'
        subprocess.run(['git', 'worktree', 'add', '--quiet', '--detach', str(path), PREPARED],
                       cwd=ROOT, check=True, capture_output=True, text=True)
        try:
            for args in PREPARATION_CHECKS:
                run = subprocess.run([sys.executable, *args], cwd=path, text=True, capture_output=True)
                require(run.returncode == 0, 'Pinned preparation gate failed: ' + ' '.join(args) +
                        '\n' + run.stdout + run.stderr)
                require(run.stderr == '', 'Unexpected preparation diagnostics: ' + run.stderr)
                results.append({'command': ['python3', *args], 'exit_code': 0,
                                'stdout': run.stdout.strip()})
        finally:
            # This path was created solely by this function; no user checkout is removed.
            subprocess.run(['git', 'worktree', 'remove', '--force', str(path)], cwd=ROOT,
                           check=True, capture_output=True, text=True)
    return results


def verify():
    require(git('rev-parse', PUBLISHED + '^').decode().strip() == PREPARED,
            'Unexpected publication lineage')
    require(subprocess.run(['git', 'merge-base', '--is-ancestor', PUBLISHED, 'HEAD'],
                           cwd=ROOT).returncode == 0, 'HEAD predates publication')
    # The published snapshot is evidence, not a working copy to silently update.
    require(not git('diff', '--name-only', PUBLISHED, '--', 'courses/86957').strip(),
            'Published snapshot changed after its receipt commit')
    require(not git('ls-files', '--others', '--exclude-standard', '--', 'courses/86957').strip(),
            'Unrecorded file in published snapshot')
    snapshot_hashes = verify_tree_files(PUBLISHED, 'courses/86957')
    mutable = {PACKAGE + '/' + name for name in ['manifest.json', 'README.md', 'CHANGES.md', 'preview.html']}
    preserved_hashes = verify_tree_files(PREPARED, PACKAGE, mutable)
    for name in ['theory-2026-11-23', 'theory-continuation-2026-11-23',
                 'theory-links-2026-11-23', 'quality-2026-11-23',
                 'assessment-2026-11-23', 'functions-2026-11-23', 'practice-2026-11-23']:
        preserved_hashes.update(verify_tree_files(PREPARED, 'improvements/86957/' + name))
    # Preserve old implementation and proof, rather than weakening its assertions.
    for path, oid in tree_files(PREPARED, 'tools').items():
        data = (ROOT / path).read_bytes()
        require(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == oid,
                'Historical tool changed: ' + path)
        preserved_hashes[path] = sha(data)

    manifest = read(PKG / 'manifest.json')
    before_manifest = json.loads(pinned(PREPARED, PACKAGE + '/manifest.json'))
    require({k: v for k, v in manifest.items() if k not in {'publication', 'status'}} ==
            {k: v for k, v in before_manifest.items() if k not in {'publication', 'status'}},
            'Publication changed accepted package membership/content')
    publication = manifest['publication']
    require(manifest['status'] == 'published' and publication['status'] == 'verified_on_stepik' and
            publication['applied'] is True and publication['source_commit'] == PREPARED and
            publication['verification_receipt'] == RECEIPT, 'Unverified publication state')
    receipt = read(ROOT / RECEIPT)
    require(receipt['status'] == 'verified' and receipt['source_commit'] == PREPARED and
            receipt['course_id'] == 86957 and receipt['package'] == PKG.name,
            'Wrong publication receipt')
    changes = {s['step_id']: s for s in manifest['steps']}
    require(len(changes) == len(manifest['steps']) == receipt['changed_steps'] == 55 and
            set(receipt['verified_step_ids']) == set(changes), 'Wrong published IDs')
    require(receipt['written_steps'] + receipt['already_at_target'] == 55 and
            receipt['unchanged_steps'] == 430 and receipt['author_steps'] == receipt['learner_steps'] == 485 and
            receipt['changed_field'] == 'block.text' and receipt['all_step_positions_verified'] is True and
            receipt['author_and_learner_projection_checked_for_all_steps'] is True,
            'Incomplete saved API-readback claims')

    course_manifest = read(ROOT / 'courses/86957/manifest.json')
    previous_course_manifest = json.loads(pinned(PREPARED, 'courses/86957/manifest.json'))
    require(course_manifest['step_files'] == previous_course_manifest['step_files'], 'Placement/bindings changed')
    bindings = {s['step_id']: s for s in course_manifest['step_files']['bindings']}
    require(len(bindings) == 485 and course_manifest['step_files']['written'] == 485,
            'Incomplete step bindings')
    bundle = read(ROOT / 'courses/86957/course.json')
    previous_bundle = json.loads(pinned(PREPARED, 'courses/86957/course.json'))
    sections = {s['id']: s for s in bundle['sections']}
    sources = {s['id']: s for s in bundle['step_sources']}
    learners = {s['id']: s for s in bundle['steps']}
    previous_sources = {s['id']: s for s in previous_bundle['step_sources']}
    require(set(sources) == set(learners) == set(bindings), 'Missing source/learner projection')
    metadata_counts = {}
    require(changed_fields(previous_bundle['course'], bundle['course']) == ['update_date'],
            'Course fields changed beyond publication metadata')
    require(bundle['course'] == read(ROOT / 'courses/86957/raw/courses/86957.json'), 'Raw course mismatch')
    for group, singular in [('sections', 'sections'), ('units', 'units'), ('lessons', 'lessons')]:
        before = {x['id']: x for x in previous_bundle[group]}
        require(set(before) == {x['id'] for x in bundle[group]}, 'Hierarchy IDs changed: ' + group)
        count = 0
        for item in bundle[group]:
            require(item == read(ROOT / f'courses/86957/raw/{singular}/{item["id"]}.json'),
                    'Raw hierarchy mismatch')
            fields = changed_fields(before[item['id']], item)
            require(fields in [[], ['update_date']], 'Hierarchy changed beyond timestamp: ' + group)
            count += bool(fields)
        metadata_counts[group + '.update_date'] = count

    prepared_files = tree_files(PREPARED, 'courses/86957/steps')
    unchanged = 0
    normalized, exact, export_times = [], [], set()
    source_counter_change = []
    current_docs = {}
    for sid, binding in bindings.items():
        source, learner = sources[sid], learners[sid]
        path = ROOT / 'courses/86957' / binding['path']
        document = read(path)
        current_docs[sid] = document
        require(source == read(ROOT / 'courses/86957' / binding['raw_step_source']) and
                learner == read(ROOT / 'courses/86957' / binding['raw_step']), 'Raw/bundle step mismatch')
        require(int(document['id']) == source['id'] == learner['id'] == sid and
                source['lesson'] == learner['lesson'] == binding['lesson_id'] and
                source['position'] == learner['position'] == binding['position'] and
                document['block'] == source['block'] and document['block']['name'] == binding['type'],
                'Step identity, placement or author block mismatch')
        projected = {k: deepcopy(v) for k, v in source.items() if k not in SOURCE_ONLY}
        projected['block'] = {k: v for k, v in projected['block'].items() if k not in SOURCE_BLOCK_ONLY}
        require(projected == learner, 'Author/learner projection mismatch')
        if sid not in changes:
            data = path.read_bytes()
            require(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() ==
                    prepared_files[path.relative_to(ROOT).as_posix()], 'Unrelated .step changed')
            require(source == previous_sources[sid], 'Unrelated author source changed')
            unchanged += 1
            continue
        require(binding['type'] == 'text' and sections[binding['section_ids'][0]]['position'] <= 19,
                'Publication outside allowed theory modules')
        old_document = json.loads(pinned(PREPARED, path.relative_to(ROOT).as_posix()))
        require(changed_fields(old_document, document) == ['block.text', 'time'],
                'Unexpected exported .step changes')
        fields = changed_fields(previous_sources[sid], source)
        wanted = ['block.text', 'update_date']
        if sid == 3215109:
            wanted = ['block.text', 'num_grades[2]', 'update_date']
            require(previous_sources[sid]['num_grades'] == [0, 0, 0, 0, 0] and
                    source['num_grades'] == [0, 0, 1, 0, 0], 'Unexpected counter drift')
            source_counter_change.append({'step_id': sid, 'field': 'num_grades[2]', 'before': 0, 'after': 1})
        require(fields == wanted, 'Unexpected author-source changes')
        require(datetime.fromisoformat(source['update_date'].replace('Z', '+00:00')) <=
                datetime.fromisoformat(document['time'].replace('Z', '+00:00')) <=
                datetime.fromisoformat(receipt['verified_at'].replace('Z', '+00:00')),
                'Export/readback timestamp order')
        export_times.add(document['time'])
        target = read(ROOT / changes[sid]['target_path'])
        expected = deepcopy(target['block'])
        if document['block']['text'] == target['block']['text']:
            exact.append(sid)
        else:
            transformed, additions = add_missing_anchor_rel(target['block']['text'])
            require(additions > 0 and document['block']['text'] == transformed, 'Unexpected HTML transformation')
            expected['text'] = transformed
            normalized.append({'step_id': sid, 'added_rel_attributes': additions,
                               'accepted_text_sha256': sha(target['block']['text'].encode()),
                               'snapshot_text_sha256': sha(transformed.encode())})
        require(document['block'] == expected, 'Publication changed other block fields')
    normalized_ids = sorted(r['step_id'] for r in normalized)
    require(unchanged == 430 and len(exact) == 48 and len(normalized) == 7 and
            normalized_ids == sorted(receipt['normalized_html_step_ids']) ==
            sorted(publication['normalized_html_step_ids']), 'Normalization/unchanged counts differ')
    require(len({r['lesson_id'] for r in changes.values()}) == manifest['changed_lessons'] ==
            receipt['changed_lessons'] == 32 and
            len({sections[bindings[sid]['section_ids'][0]]['position'] for sid in changes}) ==
            receipt['changed_modules'] == 15, 'Publication extent mismatch')

    acceptance = json.loads(pinned(PREPARED, PACKAGE + '/review_completion.json'))
    theory_ids = {sid for sid, b in bindings.items() if b['type'] == 'text' and
                  sections[b['section_ids'][0]]['position'] <= 19}
    require(len(theory_ids) == 283 and {r['step_id'] for r in acceptance['effective_inputs']} == theory_ids,
            'Theory inventory mismatch')
    locations = {(b['lesson_id'], b['position']): sid for sid, b in bindings.items()}
    links, package_links, pre_count = 0, 0, 0
    effective_hashes = {}
    for row in acceptance['effective_inputs']:
        data = pinned(PREPARED, row['path'])
        require(sha(data) == row['file_sha256'], 'Accepted input drift')
        approved = json.loads(data)
        sid = row['step_id']
        text = current_docs[sid]['block']['text']
        expected = approved['block']['text']
        if sid in normalized_ids:
            expected, _ = add_missing_anchor_rel(expected)
        require(text == expected, 'Snapshot differs from accepted theory: ' + str(sid))
        before_pre = re.findall(r'<pre\b[^>]*>.*?</pre>', approved['block']['text'], re.S)
        require(before_pre == re.findall(r'<pre\b[^>]*>.*?</pre>', text, re.S), 'Published pre changed')
        pre_count += len(before_pre)
        effective_hashes[str(sid)] = sha(text.encode())
        parser = TextLinks(); parser.feed(text)
        require(not parser.forbidden, 'Active/video element in accepted theory')
        for url in parser.urls:
            parsed = urlparse(url)
            if parsed.hostname in {'stepik.org', 'www.stepik.org'}:
                match = re.fullmatch(r'/lesson/(\d+)/step/(\d+)/?', parsed.path)
                if match:
                    require(tuple(map(int, match.groups())) in locations, 'Unresolved course link')
                    links += 1
                    package_links += sid in changes
    require(pre_count == 340 and links == 323 and package_links == receipt['internal_links_verified'] == 103,
            'Code/link coverage mismatch')

    preparation_checks = run_preparation_checks()
    current_checks = []
    for args in [['tools/build_theory_upgrade.py', '--check'], ['tools/render_course_tree.py', '--check']]:
        result = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True)
        require(result.returncode == 0 and not result.stderr, 'Current gate failed: ' + result.stdout + result.stderr)
        current_checks.append({'command': ['python3', *args], 'exit_code': 0, 'stdout': result.stdout.strip()})
    return {
        'schema_version': 1, 'status': 'passed', 'course_id': 86957,
        'prepared_commit': PREPARED, 'publication_commit': PUBLISHED,
        'evidence_mode': 'Local comparison with saved publication receipt and pinned Git snapshots; no new live Stepik read.',
        'snapshot': {'step_count': 485, 'source_and_learner_projections_verified': 485,
                     'bindings_unchanged': True, 'unrelated_step_files_byte_identical': unchanged,
                     'published_text_steps': 55, 'byte_identical_accepted_html': len(exact),
                     'exact_rel_normalizations': normalized,
                     'accepted_theory_steps': 283, 'unchanged_theory_pre_blocks': pre_count,
                     'internal_link_occurrences': links, 'package_internal_link_occurrences': package_links,
                     'all_snapshot_files_match_publication_commit': True,
                     'snapshot_files_checked': len(snapshot_hashes)},
        'metadata_changes': {'exported_step_time_fields': 55, 'export_times': sorted(export_times),
                             'raw_source_update_dates': 55, 'raw_learner_update_dates': 55,
                             'course_update_date': 1, **metadata_counts,
                             'external_api_counter_changes': source_counter_change,
                             'note': 'Export time and API update/statistical metadata are separate from lesson content and grading/checker settings.'},
        'historical_preparation': {'checks_rerun_unchanged_at_commit': PREPARED,
                                   'checks': preparation_checks,
                                   'preserved_files_checked': len(preserved_hashes),
                                   'preserved_files_index_sha256': sha(json.dumps(preserved_hashes, sort_keys=True).encode()),
                                   'new_compiler_or_program_execution_count': 0},
        'current_repository_checks': current_checks,
        'input_sha256': {path: sha((ROOT / path).read_bytes()) for path in
                         [PACKAGE + '/manifest.json', RECEIPT, 'courses/86957/manifest.json',
                          'courses/86957/course.json', 'courses/86957/TREE.md',
                          PACKAGE + '/review_completion.json', PACKAGE + '/code_coverage.json',
                          PACKAGE + '/runtime_summary.json', 'tools/verify_theory_published.py']},
        'snapshot_files_index_sha256': sha(json.dumps(snapshot_hashes, sort_keys=True).encode()),
        'effective_theory_text_index_sha256': sha(json.dumps(effective_hashes, sort_keys=True).encode()),
        'live_stepik_access': False, 'stepik_updates_performed': False,
        'limitations': ['The API readback itself is the publisher\'s saved evidence, not a new live verification by this tool.',
                        'No live HTML rendering, Windows/MSVC, macOS, graded checker or compiler test rerun is claimed.',
                        'The old preparation gates remain tied to their original commit; current snapshot checks do not rewrite their reports.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify the saved report without replacing it')
    args = parser.parse_args()
    result = verify()
    if args.check:
        require(REPORT.is_file() and read(REPORT) == result, 'Published verification report is stale')
    else:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'publication_commit': PUBLISHED,
                      'published_text_steps': 55, 'accepted_theory_steps': 283,
                      'source_and_learner_projections': 485, 'preparation_gates': 5,
                      'new_compilations': 0, 'live_stepik_access': False}))


if __name__ == '__main__':
    main()
