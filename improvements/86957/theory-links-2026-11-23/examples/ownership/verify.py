#!/usr/bin/env python3
"""Check the LINKS ownership review and its new author-only demonstration."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import platform
import re
import subprocess
import tempfile
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
ROOT = PACKAGE.parents[2]
COURSE = ROOT / 'courses/86957'


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.urls.append(dict(attrs).get('href', ''))


def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True,
                            text=True, timeout=45)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path,
                        default=PACKAGE / 'validation/ownership.json')
    args = parser.parse_args()
    report = {
        'schema_version': 1,
        'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat(),
        'scope': '59 reviewed text steps in modules 12–15; seven prose/link edits; unchanged lesson code; new author-only base-destruction harness',
        'standards': ['c++17', 'c++20'],
        'counts': {'reviewed_inputs': 0, 'related_reviewed_inputs': 0, 'changed_steps': 0,
                   'unchanged_pre_blocks': 0, 'course_links': 0,
                   'compilations': 0, 'runtime_cases': 0},
        'runs': [],
        'limitations': [
            'No live Stepik access or publication verification.',
            'No full rerun of historical T5/T5B suites; existing lesson code is byte-identical.',
            'GCC/Linux with UBSan only; Windows/MSVC and macOS were not tested.',
            'The invalid deletion of Derived through a non-virtual Base* is explained from the standard and never executed.',
        ],
    }
    try:
        review_path = PACKAGE / 'review_ownership.json'
        review = json.loads(review_path.read_text())
        changes_path = PACKAGE / 'changes_ownership.json'
        changes = json.loads(changes_path.read_text())
        bindings = json.loads((COURSE / 'manifest.json').read_text())['step_files']['bindings']
        by_id = {r['step_id']: r for r in bindings}
        locations = {(r['lesson_id'], r['position']): r['step_id'] for r in bindings}
        bundle = json.loads((COURSE / 'course.json').read_text())
        published = {row['id']: row for row in bundle['step_sources']}
        sections = {row['id']: row['position'] for row in bundle['sections']}
        target_ids = {r['step_id'] for r in bindings if r['type'] == 'text'
                      and any(sections[s] in {12, 13, 14, 15} for s in r['section_ids'])}
        assert set(review['reviewed_text_step_ids']) == target_ids
        assert set(review['changed_text_step_ids']) == {r['step_id'] for r in changes}
        input_hashes = {}
        for item in review['review_inputs'] + review['related_review_inputs']:
            path = ROOT / item['source_path']
            raw = path.read_bytes()
            before = json.loads(raw)
            assert digest(raw) == item['file_sha256'], item['step_id']
            assert digest(before['block']['text'].encode()) == item['text_sha256']
            assert before['block'] == published[item['step_id']]['block']
            input_hashes[item['source_path']] = digest(raw)
            counter = ('reviewed_inputs' if item['step_id'] in target_ids
                       else 'related_reviewed_inputs')
            report['counts'][counter] += 1
        for row in changes:
            assert row['step_id'] in target_ids
            baseline = COURSE / row['path']
            target = PACKAGE / row['path']
            before = json.loads(baseline.read_bytes())
            after = json.loads(target.read_bytes())
            assert before['block']['name'] == after['block']['name'] == 'text'
            old_text, new_text = before['block']['text'], after['block']['text']
            assert old_text != new_text
            before['block']['text'] = new_text
            assert before == after, ('Only block.text may change', row['step_id'])
            old_pre = re.findall(r'<pre\b[^>]*>[\s\S]*?</pre>', old_text)
            new_pre = re.findall(r'<pre\b[^>]*>[\s\S]*?</pre>', new_text)
            assert old_pre == new_pre, ('Code/output block changed', row['step_id'])
            report['counts']['unchanged_pre_blocks'] += len(old_pre)
            report['counts']['changed_steps'] += 1
            input_hashes[str(target.relative_to(ROOT))] = digest(target.read_bytes())
        changes_by_id = {r['step_id']: r for r in changes}
        for sid in target_ids:
            path = (PACKAGE / changes_by_id[sid]['path'] if sid in changes_by_id
                    else COURSE / by_id[sid]['path'])
            links = Links()
            links.feed(json.loads(path.read_text())['block']['text'])
            for url in links.urls:
                parsed = urlparse(url)
                if parsed.hostname == 'stepik.org':
                    match = re.fullmatch(r'/lesson/(\d+)/step/(\d+)/?', parsed.path)
                    if match:
                        assert tuple(map(int, match.groups())) in locations, (sid, url)
                        report['counts']['course_links'] += 1
        report['compiler'] = run(['g++', '--version']).stdout.splitlines()[0]
        report['platform'] = platform.platform()
        source = HERE / 'base_destruction.cpp'
        for path in [source, Path(__file__), review_path, changes_path]:
            input_hashes[str(path.relative_to(ROOT))] = digest(path.read_bytes())
        report['input_sha256'] = input_hashes
        cases = ['unique_normal', 'unique_empty', 'shared_convert', 'shared_direct']
        with tempfile.TemporaryDirectory(prefix='links-ownership-') as temp:
            for standard in report['standards']:
                binary = Path(temp) / standard
                flags = ['g++', '-std=' + standard, '-Wall', '-Wextra',
                         '-Wpedantic', '-Werror', '-UNDEBUG', '-O1', '-g',
                         '-fsanitize=undefined', '-fno-sanitize-recover=all']
                result = run(flags + [source, '-o', binary])
                assert result.returncode == 0, result.stderr
                report['counts']['compilations'] += 1
                report.setdefault('compile_flags', flags[2:])
                for case in cases + ['unknown']:
                    result = run([binary, case])
                    expected_code = 2 if case == 'unknown' else 0
                    expected_output = '' if case == 'unknown' else case + ' passed\n'
                    assert (result.returncode, result.stdout, result.stderr) == (
                        expected_code, expected_output, ''), (case, result)
                    report['counts']['runtime_cases'] += 1
                    report['runs'].append({'standard': standard, 'case': case,
                                           'exit_code': result.returncode,
                                           'stdout': result.stdout, 'stderr': result.stderr})
        report['status'] = 'passed'
        report['passed'] = True
    except Exception as error:
        report['status'] = 'failed'
        report['passed'] = False
        report['error'] = repr(error)
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'counts': report['counts'],
                      'report': str(args.report)}, ensure_ascii=False))
    if not report['passed']:
        raise SystemExit(report['error'])


if __name__ == '__main__':
    main()
