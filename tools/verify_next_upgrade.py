#!/usr/bin/env python3
"""Regenerate local verification for the functions/practice upgrade.

Each child report is invalidated before its verifier runs. This command never
publishes to Stepik and does not change the historical validation.json.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REVISION = ROOT / 'improvements/86957'
FUNCTIONS = REVISION / 'functions-2026-11-23'
PRACTICE = REVISION / 'practice-2026-11-23'
REPORT = REVISION / 'validation_next.json'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hashes():
    paths = {ROOT / 'tools/build_next_upgrade.py', ROOT / 'tools/build_quality_packages.py',
             Path(__file__).resolve(), ROOT / 'courses/86957/manifest.json'}
    for package in (FUNCTIONS, PRACTICE):
        for path in package.rglob('*'):
            if (path.is_file() and '__pycache__' not in path.parts
                    and not path.name.startswith('validation')
                    and path.suffix in {'.json', '.step', '.cpp', '.hpp', '.py', '.md', '.html'}):
                paths.add(path)
        manifest = json.loads((package / 'manifest.json').read_text())
        paths.update(ROOT / step['source_path'] for step in manifest['steps'])
    # The new algorithm questions rely on these previously validated lessons.
    dependency = REVISION / 'quality-2026-11-23'
    paths.add(dependency / 'manifest.json')
    paths.update((dependency / 'steps').glob('*/*.step'))
    return {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(paths)}


def command(arguments, report, label, timeout=180):
    result = subprocess.run([sys.executable, *arguments], cwd=ROOT, text=True,
                            capture_output=True, timeout=timeout)
    record = {'label': label, 'command': arguments, 'returncode': result.returncode,
              'stdout': result.stdout[-6000:], 'stderr': result.stderr[-6000:]}
    report['commands'].append(record)
    write_json(REPORT, report)
    require(result.returncode == 0, f'{label} failed: {record["stdout"]} {record["stderr"]}')
    print(f'{label}: passed', flush=True)


def child(script, child_report, report, label):
    write_json(child_report, {'status': 'running', 'all_passed': False,
                              'reason': 'Invalidated by verify_next_upgrade.py before child invocation'})
    command([script.relative_to(ROOT).as_posix()], report, label)
    data = json.loads(child_report.read_text())
    require(data.get('status') == 'passed' and data.get('all_passed') is True,
            f'{label}: child did not produce a successful report')
    hashes = data.get('input_sha256')
    require(isinstance(hashes, dict) and bool(hashes), f'{label}: no recorded input hashes')
    for name, expected in hashes.items():
        candidates = [(ROOT / name).resolve(), (script.parent / name).resolve()]
        matching = [path for path in candidates if path.is_relative_to(ROOT) and path.is_file()
                    and sha(path) == expected]
        require(bool(matching), f'{label}: stale or invalid input hash: {name}')
    report['children'][label] = {
        'report': child_report.relative_to(ROOT).as_posix(), 'sha256': sha(child_report),
        'status': data['status'],
        'counts': data.get('counts', {key: data[key] for key in
                   ('compilations', 'runtime_cases', 'checker_negative_probes') if key in data}),
    }
    write_json(REPORT, report)


def main():
    report = {'schema_version': 1, 'course_id': 86957, 'date': '2026-11-23',
              'base_commit': '498e5468863becfdf72f5c73ca52bd2ebfeaf229',
              'status': 'running', 'all_passed': False, 'commands': [], 'children': {},
              'scope': 'New functions and assessed practice packages; local validation only.',
              'live_stepik_verified': False}
    write_json(REPORT, report)
    try:
        initial = input_hashes()
        report['input_sha256'] = initial
        write_json(REPORT, report)
        command(['tools/build_next_upgrade.py', '--check'], report, 'package_integrity')
        command(['tools/build_quality_packages.py', '--check'], report, 'previous_dependency_integrity')
        child(FUNCTIONS / 'verify.py', FUNCTIONS / 'validation.json', report, 'functions')
        child(PRACTICE / 'verify.py', PRACTICE / 'validation.json', report, 'algorithm_assessments')
        child(PRACTICE / 'verify_entry.py', PRACTICE / 'validation_entry.json', report, 'cpp_entry')
        require(input_hashes() == initial, 'Verification inputs changed during this run')
        function_counts = report['children']['functions']['counts']
        algorithm_counts = report['children']['algorithm_assessments']['counts']
        entry_counts = report['children']['cpp_entry']['counts']
        counts = {
            'changed_steps': sum(json.loads((package / 'manifest.json').read_text())['changed_steps']
                                 for package in (FUNCTIONS, PRACTICE)),
            'compilations': sum(child['counts']['compilations'] for child in report['children'].values()),
            'runtime_cases': sum(child['counts']['runtime_cases'] for child in report['children'].values()),
            'function_programs': function_counts['programs'],
            'function_program_runs': function_counts['runtime_cases'],
            'algorithm_reference_runs': algorithm_counts['reference_cases'],
            'algorithm_generated_cases': algorithm_counts['generated_cases'],
            'incorrect_algorithms_rejected': algorithm_counts['negative_probes'],
            'algorithm_checker_probes': algorithm_counts['checker_probes'],
            'entry_reference_runs': entry_counts['runtime_cases'],
            'entry_checker_negative_probes': entry_counts['checker_negative_probes'],
        }
        report.update(status='passed', all_passed=True, counts=counts)
        write_json(REPORT, report)
        print(json.dumps({'status': report['status'], 'counts': counts}, ensure_ascii=False))
        return 0
    except Exception as error:
        report.update(status='failed', all_passed=False, error=f'{type(error).__name__}: {error}')
        write_json(REPORT, report)
        print(report['error'], file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
