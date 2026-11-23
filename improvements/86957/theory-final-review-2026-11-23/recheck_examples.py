#!/usr/bin/env python3
"""Rerun all eleven saved theory suites in isolated worktrees.

Original package files and reports remain untouched. Runtime reports retain
their declared historical source scope; effective HTML coverage is established
separately, by content equality and the independent editorial inventories.
No Stepik operation is performed.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '26bbfeb5065ef3475f9ea612a3a8785f934b7c49'
LEGACY_COURSE = 'd96e5b9cffa65010c53894a9b65b1a497cb6b58a'
SUITES = [
    ('t1', 'theory-2026-11-23', 't1', 'examples/t1/validation.json'),
    ('t3', 'theory-2026-11-23', 't3', 'examples/t3/validation.json'),
    ('t6', 'theory-2026-11-23', 't6', 'examples/t6/validation.json'),
    ('t1b', 'theory-continuation-2026-11-23', 't1b', 'examples/t1b/validation.json'),
    ('t2', 'theory-continuation-2026-11-23', 't2', 'examples/t2/validation.json'),
    ('t4', 'theory-continuation-2026-11-23', 't4', 'examples/t4/validation.json'),
    ('t5', 'theory-continuation-2026-11-23', 't5', 'examples/t5/validation.json'),
    ('t5b', 'theory-continuation-2026-11-23', 't5b', 'examples/t5b/validation.json'),
    ('links_types', 'theory-links-2026-11-23', 'types', 'examples/types/validation.json'),
    ('links_ownership', 'theory-links-2026-11-23', 'ownership', 'validation/ownership.json'),
    ('links_algorithms', 'theory-links-2026-11-23', 'algorithms', 'validation/algorithms_current.json'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')


def git(folder, *arguments):
    return subprocess.check_output(['git', '-C', str(folder), *arguments], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy-worktree', type=Path, required=True)
    parser.add_argument('--links-worktree', type=Path, required=True)
    parser.add_argument('--cmake', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2, choices=[1, 2, 3])
    args = parser.parse_args()
    for folder in [args.legacy_worktree, args.links_worktree]:
        assert folder.resolve() != ROOT.resolve(), 'Do not run in the canonical checkout'
        assert git(folder, 'rev-parse', 'HEAD') == BASE, 'Unexpected suite checkout'
    assert args.cmake.is_file(), 'Provide the real CMake binary with adjacent ctest'
    assert args.cmake.with_name('ctest').is_file()
    # T1B checks a before/after difference directly against courses; faithfully
    # recreate its pre-publication snapshot instead of weakening that assertion.
    legacy_paths = subprocess.check_output(
        ['git', '-C', str(ROOT), 'ls-tree', '-r', LEGACY_COURSE, '--', 'courses/86957'],
        text=True).splitlines()
    for line in legacy_paths:
        metadata, relative = line.split('\t', 1)
        expected_blob = metadata.split()[2]
        actual = args.legacy_worktree / relative
        assert actual.is_file(), relative
        raw = actual.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        assert blob == expected_blob, 'Legacy course reconstruction drift: ' + relative
    output = HERE / 'validation/recheck'
    output.mkdir(parents=True, exist_ok=True)
    original_reports = {str(ROOT / 'improvements/86957' / package / report):
                        sha(ROOT / 'improvements/86957' / package / report)
                        for _, package, _, report in SUITES}
    summary = {
        'schema_version': 1, 'status': 'running', 'started_at': now(),
        'base_commit': BASE, 'legacy_course_snapshot': LEGACY_COURSE,
        'scope': 'New isolated execution of all eleven existing theory author suites; not a blanket claim about every HTML fragment.',
        'python': sys.version.split()[0],
        'cmake': subprocess.check_output([str(args.cmake), '--version'], text=True).splitlines()[0],
        'legacy_worktree': str(args.legacy_worktree), 'links_worktree': str(args.links_worktree),
        'runner_sha256': sha(Path(__file__)), 'suites': [],
        'historical_reports_before_sha256': original_reports,
        'stepik_access': False,
    }
    save(output / 'summary.json', summary)
    environment = os.environ.copy()
    environment['CMAKE'] = str(args.cmake)
    environment['LC_ALL'] = 'C'

    def run_suite(spec):
        name, package, part, report_relative = spec
        folder = args.links_worktree if name.startswith('links_') else args.legacy_worktree
        package_path = Path('improvements/86957') / package
        relative = package_path / 'examples' / part / 'verify.py'
        assert sha(folder / relative) == sha(ROOT / relative), 'Verifier differs from saved source'
        command = [sys.executable, str(folder / relative)]
        record = {'name': name, 'started_at': now(), 'command': command,
                  'verifier_path': str(relative), 'verifier_sha256': sha(ROOT / relative),
                  'source_package': str(package_path), 'output_report': str(output / (name + '.json'))}
        try:
            result = subprocess.run(command, cwd=folder, env=environment, text=True,
                                    capture_output=True, timeout=1200)
            record.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
            source_report = folder / package_path / report_relative
            shutil.copyfile(source_report, output / (name + '.json'))
            document = json.loads(source_report.read_text())
            record['reported_status'] = document['status']
            record['report_sha256'] = sha(output / (name + '.json'))
            record['status'] = 'passed' if result.returncode == 0 and document['status'] == 'passed' else 'failed'
            if name == 't3':
                gtests = [c for c in document.get('checks', [])
                          if isinstance(c, str) and c.startswith('GoogleTest pinned version,')]
                record['google_test_standards_verified'] = len(gtests)
                if len(gtests) != 2:
                    record['status'] = 'incomplete_dependency_check'
        except Exception as error:
            record.update(status='failed', error=f'{type(error).__name__}: {error}')
        record['finished_at'] = now()
        save(output / (name + '_execution.json'), record)
        return record

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_suite, spec) for spec in SUITES]
        for future in as_completed(futures):
            result = future.result()
            summary['suites'].append(result)
            save(output / 'summary.json', summary)
            print(json.dumps({'suite': result['name'], 'status': result['status']}, ensure_ascii=False), flush=True)
    summary['suites'].sort(key=lambda row: row['name'])
    summary['historical_reports_unchanged'] = all(sha(Path(path)) == digest
                                                for path, digest in original_reports.items())
    summary['status'] = ('passed' if summary['historical_reports_unchanged'] and
                         all(s['status'] == 'passed' for s in summary['suites']) else 'failed_or_incomplete')
    summary['finished_at'] = now()
    save(output / 'summary.json', summary)
    print(json.dumps({'status': summary['status'], 'suites': len(summary['suites']),
                      'historical_reports_unchanged': summary['historical_reports_unchanged']}), flush=True)
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
