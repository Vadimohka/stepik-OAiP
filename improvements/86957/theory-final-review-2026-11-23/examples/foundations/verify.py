#!/usr/bin/env python3
"""Author checks for three foundations clarifications; no Stepik operations."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
ROOT = PACKAGE.parents[2]
FLAGS = ['-Wall', '-Wextra', '-Wpedantic', '-Werror', '-O2',
         '-fsanitize=undefined', '-fno-sanitize-recover=all']
BINDINGS = {
    'integer_division.cpp': (3177291, 1), 'if_input.cpp': (3177292, 1),
    'wide_characters.cpp': (3177281, 1), 'narrow_casts.cpp': (3177281, 2),
    'type_sizes.cpp': (3177283, 1),
}


class PreBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'pre' and self.current is not None:
            self.blocks.append(''.join(self.current))
            self.current = None


def blocks(text):
    parser = PreBlocks()
    parser.feed(text)
    return parser.blocks


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, stdin=''):
    environment = os.environ.copy()
    environment['LC_ALL'] = 'C'
    return subprocess.run(list(map(str, args)), input=stdin, text=True,
                          capture_output=True, timeout=30, env=environment)


def successful(args):
    result = run(args)
    assert result.returncode == 0, result.stderr
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path,
                    default=PACKAGE / 'validation/new_foundations.json')
    args = ap.parse_args()
    compiler = os.environ.get('CXX', 'g++')
    report = {
        'schema_version': 1,
        'part': 'VERIFY_FOUNDATIONS',
        'started_at': datetime.now(timezone.utc).isoformat(),
        'status': 'running',
        'standards': ['c++17', 'c++20'],
        'platform': platform.platform(),
        'python': sys.version.split()[0],
        'flags': FLAGS,
        'historical_reports_replaced': False,
        'scope': 'Three prose-only corrections; five unchanged exact lesson programs '
                 '(including three previously uncovered full listings), '
                 'one author-only numerical-contract harness, and rejected constant expressions.',
        'counts': {'source_inputs_verified': 0, 'changed_steps_verified': 0,
                   'unchanged_pre_blocks': 0, 'exact_program_bindings': 0,
                   'successful_compilations': 0, 'runtime_cases': 0,
                   'expected_compile_failures': 0},
        'runtime_cases': [],
        'expected_compile_failures': [],
        'limitations': [
            'This targeted run does not compile every program or fragment in all 96 reviewed texts.',
            'All five bound course programs are unchanged; two have corrected surrounding explanations, three supply missing author-run coverage.',
            'Executed on the recorded Linux/GCC platform and C locale; Windows/MSVC and macOS were not executed.',
            'The minimum / -1 and minimum % -1 rejection fixtures require the recorded two-complement int range; the harness verifies that assumption.',
            'Undefined arithmetic is never executed; invalid expressions are tested only as rejected constant expressions.',
            'No Stepik operation or modification of courses, grading, video, or historical validation files.',
        ],
    }

    def save():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    try:
        report['compiler'] = successful([compiler, '--version']).stdout.splitlines()[0]
        successful([sys.executable, PACKAGE / 'authoring/foundations.py', '--check'])
        input_file = PACKAGE / 'review_inputs.json'
        source_rows = [row for row in json.loads(input_file.read_text())['steps']
                       if row['module_number'] in [1, 2, 3, 4]]
        assert len(source_rows) == 96
        inputs = {row['step_id']: row for row in source_rows}
        for row in source_rows:
            source = ROOT / row['effective_path']
            assert digest(source) == row['file_sha256'], source
            text = json.loads(source.read_text())['block']['text']
            assert hashlib.sha256(text.encode('utf-8')).hexdigest() == row['text_sha256']
            report['counts']['source_inputs_verified'] += 1

        journal = PACKAGE / 'changes_foundations.json'
        changes = json.loads(journal.read_text())
        assert {row['step_id'] for row in changes} == {3177282, 3177291, 3177292}
        targets = {}
        for change in changes:
            sid = change['step_id']
            source_row = inputs[sid]
            assert change['previous_effective_path'] == source_row['effective_path']
            assert change['previous_effective_sha256'] == source_row['file_sha256']
            previous = json.loads((ROOT / source_row['effective_path']).read_text())
            current = json.loads((PACKAGE / change['path']).read_text())
            targets[sid] = current
            assert previous['block']['name'] == current['block']['name'] == 'text'
            assert previous['block']['text'] != current['block']['text']
            assert blocks(previous['block']['text']) == blocks(current['block']['text'])
            report['counts']['unchanged_pre_blocks'] += len(blocks(current['block']['text']))
            restored = copy.deepcopy(current)
            restored['block']['text'] = previous['block']['text']
            assert restored == previous, sid
            report['counts']['changed_steps_verified'] += 1
        for filename, (sid, index) in BINDINGS.items():
            effective = targets.get(sid)
            if effective is None:
                effective = json.loads((ROOT / inputs[sid]['effective_path']).read_text())
            assert (HERE / filename).read_text() == blocks(effective['block']['text'])[index]
            report['counts']['exact_program_bindings'] += 1

        files = [input_file, journal, PACKAGE / 'authoring/foundations.py',
                 HERE / 'verify.py', HERE / 'README.md', HERE / 'numeric_contracts.cpp']
        files += [HERE / filename for filename in BINDINGS]
        files += [PACKAGE / change['path'] for change in changes]
        files += [ROOT / inputs[sid]['effective_path'] for sid in {3177281, 3177283}]
        initial_hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in files}
        report['input_sha256'] = initial_hashes
        with tempfile.TemporaryDirectory(prefix='theory-foundations-') as temporary:
            directory = Path(temporary)
            for standard in report['standards']:
                binaries = {}
                for filename in [*BINDINGS, 'numeric_contracts.cpp']:
                    binary = directory / f'{Path(filename).stem}-{standard}'
                    successful([compiler, '-std=' + standard, *FLAGS, HERE / filename, '-o', binary])
                    binaries[filename] = binary
                    report['counts']['successful_compilations'] += 1

                contract = successful([binaries['numeric_contracts.cpp']])
                assert contract.stderr == ''
                values = json.loads(contract.stdout)
                assert values['valid_division_pairs'] == 40200
                report.setdefault('platform_contracts', {})[standard] = values
                report['counts']['runtime_cases'] += 1
                report['runtime_cases'].append({'standard': standard, 'program': 'numeric_contracts.cpp',
                                               'case': 'numeric-types-and-40200-valid-pairs', 'status': 'passed'})

                fixed_outputs = {
                    'wide_characters.cpp': 'He\n',
                    'narrow_casts.cpp': 'Helo\n',
                    'type_sizes.cpp': f"Bits per byte: {values['char_bit']}\n"
                                      f"sizeof(number) = {values['long_double_bytes']}\n"
                                      f"int range: {values['int_min']} ... {values['int_max']}\n",
                }
                for filename, expected in fixed_outputs.items():
                    result = run([binaries[filename]])
                    assert (result.returncode, result.stdout, result.stderr) == (0, expected, ''), (filename, result)
                    report['counts']['runtime_cases'] += 1
                    report['runtime_cases'].append({'standard': standard, 'program': filename,
                                                   'case': 'documented-output-on-recorded-platform', 'status': 'passed'})

                condition_cases = [
                    ('negative', '-2\n', 0, 'negative\n0\n'),
                    ('zero', '0\n', 0, 'zero\n1\n'),
                    ('positive', '2\n', 0, 'positive\n1\n'),
                    ('numeric-prefix', '12x\n', 0, 'positive\n1\n'),
                    ('negative-prefix', '  -2tail\n', 0, 'negative\n0\n'),
                    ('unused-second-number', '0 9\n', 0, 'zero\n1\n'),
                    ('end-without-newline', '2', 0, 'positive\n1\n'),
                    ('empty', '', 1, 'INVALID\n'),
                    ('whitespace-only', ' \t\n', 1, 'INVALID\n'),
                    ('invalid-first-character', 'abc\n', 1, 'INVALID\n'),
                    ('sign-without-digits', '+\n', 1, 'INVALID\n'),
                    ('int-min', str(values['int_min']), 0, 'negative\n0\n'),
                    ('int-max', str(values['int_max']), 0, 'positive\n1\n'),
                    ('below-int-min', str(values['int_min'] - 1), 1, 'INVALID\n'),
                    ('above-int-max', str(values['int_max'] + 1), 1, 'INVALID\n'),
                ]
                division_cases = [
                    ('negative-dividend', '-7 2', 0, '-3 -1\n'),
                    ('negative-divisor', '7 -2', 0, '-3 1\n'),
                    ('both-negative', '-7 -2', 0, '3 -1\n'),
                    ('zero-dividend', '0 1', 0, '0 0\n'),
                    ('lower-bound-and-negative-unit', '-100 -1', 0, '100 0\n'),
                    ('upper-bound-and-positive-unit', '100 1', 0, '100 0\n'),
                    ('extreme-opposite-signs', '-100 100', 0, '-1 0\n'),
                    ('zero-divisor', '7 0', 1, 'INVALID\n'),
                    ('dividend-below-range', '-101 2', 1, 'INVALID\n'),
                    ('dividend-above-range', '101 2', 1, 'INVALID\n'),
                    ('divisor-below-range', '7 -101', 1, 'INVALID\n'),
                    ('divisor-above-range', '7 101', 1, 'INVALID\n'),
                    ('missing-divisor', '7', 1, 'INVALID\n'),
                    ('invalid-divisor', '7 x', 1, 'INVALID\n'),
                    ('empty', '', 1, 'INVALID\n'),
                    ('unused-tail', '-7 2x', 0, '-3 -1\n'),
                ]
                for filename, cases in [('if_input.cpp', condition_cases),
                                        ('integer_division.cpp', division_cases)]:
                    for label, stdin, returncode, stdout in cases:
                        actual = run([binaries[filename]], stdin)
                        assert (actual.returncode, actual.stdout, actual.stderr) == (returncode, stdout, ''), (standard, filename, label, actual)
                        report['counts']['runtime_cases'] += 1
                        report['runtime_cases'].append({'standard': standard, 'program': filename,
                                                       'case': label, 'status': 'passed'})

                # Constant-expression diagnostics establish rejection without
                # evaluating undefined division or remainder at run time.
                for name, expression in {
                    'minimum-divide-minus-one': 'std::numeric_limits<int>::min() / -1',
                    'minimum-remainder-minus-one': 'std::numeric_limits<int>::min() % -1',
                    'division-by-zero': '7 / 0',
                    'remainder-by-zero': '7 % 0',
                }.items():
                    source = '#include <limits>\n' \
                        'static_assert(std::numeric_limits<int>::min() + std::numeric_limits<int>::max() == -1);\n' \
                        f'constexpr int rejected = {expression};\n'
                    path = directory / f'{name}.cpp'
                    path.write_text(source)
                    result = run([compiler, '-std=' + standard, '-pedantic-errors', '-fsyntax-only', path])
                    assert result.returncode != 0 and result.stderr, (name, standard)
                    report['counts']['expected_compile_failures'] += 1
                    report['expected_compile_failures'].append({
                        'standard': standard, 'case': name, 'expression': expression,
                        'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                        'status': 'correctly_rejected',
                    })
        assert initial_hashes == {p.relative_to(ROOT).as_posix(): digest(p) for p in files}
        report['status'] = 'passed'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        save()
    print(json.dumps({'status': report['status'], **report['counts']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
