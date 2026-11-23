#!/usr/bin/env python3
"""Compile the lesson programs and check examples and generated boundary cases."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent


def run_program(binary: Path, case: dict) -> None:
    completed = subprocess.run(
        [str(binary)], input=case['stdin'], text=True, capture_output=True, timeout=5
    )
    expected = (case.get('returncode', 0), case['stdout'], case.get('stderr', ''))
    actual = (completed.returncode, completed.stdout, completed.stderr)
    if actual != expected:
        raise RuntimeError(f"{binary.name}, {case['name']}: expected {expected!r}, got {actual!r}")


def generated_cases(source: str) -> list[dict]:
    generator = random.Random(86957)
    sorting = source in {
        'standard_sort.cpp', 'bubble_sort.cpp', 'insertion_sort.cpp',
        'merge_sort.cpp', 'heap_sort.cpp',
    }
    searching = source in {'linear_search.cpp', 'binary_search.cpp'}
    if not (sorting or searching):
        return []
    result = []
    for trial in range(52):
        size = (0, 1, 2, 3, 4, 5, 8, 16, 31, 32, 63, 64, 127)[trial % 13]
        values = [generator.randint(-15, 15) for _ in range(size)]
        if source == 'binary_search.cpp':
            values.sort()
        data = f'{size}\n' + ' '.join(map(str, values)) + '\n'
        if sorting:
            output = ' '.join(map(str, sorted(values))) + '\n'
        else:
            key = generator.randint(-17, 17)
            data += f'{key}\n'
            output = f'{values.index(key)}\n' if key in values else 'not found\n'
        result.append({'name': f'generated-{trial}', 'stdin': data, 'stdout': output})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='g++')
    parser.add_argument('--report', type=Path, default=HERE / 'validation.json')
    args = parser.parse_args()
    report = {'status': 'running', 'all_passed': False, 'results': []}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    specifications = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))['examples']
    compiler = subprocess.run(
        [args.compiler, '--version'], text=True, capture_output=True, check=True
    ).stdout.splitlines()[0]
    inputs = [HERE / entry['source'] for entry in specifications] + [HERE / 'cases.json', Path(__file__)]
    report.update({
        'compiler': compiler,
        'flags': ['-Wall', '-Wextra', '-Wpedantic', '-Werror', '-O2'],
        'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    })
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='stepik-algorithms-') as folder:
        for standard in ('c++17', 'c++20'):
            for specification in specifications:
                source = HERE / specification['source']
                binary = Path(folder) / (source.stem + '-' + standard)
                subprocess.run(
                    [args.compiler, f'-std={standard}', *report['flags'], str(source), '-o', str(binary)],
                    text=True, capture_output=True, check=True, timeout=30,
                )
                fixed = specification['cases']
                generated = generated_cases(source.name)
                for case in fixed + generated:
                    run_program(binary, case)
                report['results'].append({
                    'source': source.name, 'standard': standard,
                    'fixed_cases': len(fixed), 'generated_cases': len(generated), 'passed': True,
                })
    report['status'] = 'passed'
    report['all_passed'] = True
    report['program_runs'] = sum(r['fixed_cases'] + r['generated_cases'] for r in report['results'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'builds': len(report['results']), 'program_runs': report['program_runs']}))


if __name__ == '__main__':
    main()
