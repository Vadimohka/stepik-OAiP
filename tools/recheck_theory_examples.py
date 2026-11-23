#!/usr/bin/env python3
"""Rerun published author checks without replacing historical validation files.

Each unchanged verifier runs against an isolated copy of the published package.
New reports identify the exact input hashes and the current host. No Stepik API
is used. Optional network-dependent checks retain their explicit limitations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'improvements/86957/theory-2026-11-23'
OUTPUT = ROOT / 'improvements/86957/theory-continuation-2026-11-23/validation/recheck'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parts', nargs='+', choices=['t1', 't3', 't6'],
                        default=['t1', 't3', 't6'])
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    before = {str(p.relative_to(SOURCE)): sha(p) for p in SOURCE.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts}
    failed = False
    for part in args.parts:
        started = datetime.now(timezone.utc).isoformat()
        with tempfile.TemporaryDirectory(prefix='published-recheck-', dir=ROOT.parent) as td:
            destination = Path(td) / 'improvements/86957/theory-2026-11-23'
            shutil.copytree(SOURCE, destination, ignore=shutil.ignore_patterns('__pycache__'))
            verifier = destination / f'examples/{part}/verify.py'
            result = subprocess.run([sys.executable, str(verifier)], cwd=destination,
                                    capture_output=True, text=True, timeout=900)
            report_path = destination / f'examples/{part}/validation.json'
            report = json.loads(report_path.read_text()) if report_path.exists() else None
            passed = result.returncode == 0 and report and report.get('status') == 'passed'
            failed = failed or not passed
            record = {
                'schema_version': 1, 'part': part,
                'status': 'passed' if passed else 'failed',
                'started_at': started,
                'finished_at': datetime.now(timezone.utc).isoformat(),
                'source_package': str(SOURCE.relative_to(ROOT)),
                'source_commit_at_recovery': 'd96e5b9cffa65010c53894a9b65b1a497cb6b58a',
                'verifier_sha256': before[f'examples/{part}/verify.py'],
                'historical_validation_sha256': before[f'examples/{part}/validation.json'],
                'historical_report_preserved': True,
                'host': platform.platform(), 'python': sys.version.split()[0],
                'cmake': os.environ.get('CMAKE') or shutil.which('cmake'),
                'returncode': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr,
                'current_run': report,
            }
            save(args.output / f'{part}.json', record)
            print(json.dumps({'part': part, 'status': record['status'],
                              'report': str((args.output / f'{part}.json').relative_to(ROOT))}),
                  flush=True)
    after = {str(p.relative_to(SOURCE)): sha(p) for p in SOURCE.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    if before != after:
        raise RuntimeError('Published package changed during revalidation')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
