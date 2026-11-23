#!/usr/bin/env python3
"""Author verification of T5B explanations; no Stepik writes or learner tasks."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import platform
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
ROOT = PACKAGE.parents[2]


class Codes(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.code = None
        self.codes = []

    def handle_starttag(self, tag, attrs):
        if tag == 'code' and dict(attrs).get('class') == 'language-cpp':
            self.code = []

    def handle_data(self, value):
        if self.code is not None:
            self.code.append(value)

    def handle_endtag(self, tag):
        if tag == 'code' and self.code is not None:
            self.codes.append(''.join(self.code))
            self.code = None


# The code block indices are zero-based C++ blocks; surrounding text states
# whether these are complete programs or parts assembled in the given order.
BINDINGS = {
    'reference_overloads.cpp': (3569919, [0]),
    'copy_value.cpp': (3569324, [0]),
    'guaranteed_elision.cpp': (3569932, [0]),
    'rule_zero.cpp': (4040986, [0]),
    'forwarding.cpp': (4040986, [1]),
    'storage_duration.cpp': (3569325, [0]),
    'raii.cpp': (3569964, [1]),
    'unique_access.cpp': (3569963, [0]),
    'learning_owner.cpp': (3570166, [0]),
    'shared_lifetime.cpp': (3569327, [0]),
    'teaching_shared.cpp': (3570213, [0, 1]),
}
OUTPUTS = {
    'reference_overloads.cpp': 'const lvalue reference: 7\nrvalue reference: 7\nconst lvalue reference: 8\nrvalue reference: 8\nconst lvalue reference: 9\n7 8 9\n',
    'copy_value.cpp': '4 1\n2 3\n',
    'guaranteed_elision.cpp': '42\n',
    'rule_zero.cpp': '1 4\nA 2\nB 3\n',
    'forwarding.cpp': 'const lvalue reference: 3\nrvalue reference: 2\nrvalue reference: 3\nstill present: 3\n',
    'storage_duration.cpp': '3 20\n',
    'unique_access.cpp': '10\n42\nfalse true\n42\nfalse\n',
    'learning_owner.cpp': '42\n0\n2\n0\n',
    'shared_lifetime.cpp': '2\n1\n42\nfalse true\ntrue false\n',
    'teaching_shared.cpp': '2\ntrue\nfalse\n',
    'ownership_contracts.cpp': 'ownership and reference contracts passed\n',
}
PREFIX = 'create local\ncreate dynamic\n'
SUFFIX = 'destroy dynamic\ndestroy local\n'
RAII_CASES = [
    ('normal\n', 0, PREFIX + 'normal end\n' + SUFFIX + 'done\n'),
    ('early\n', 0, PREFIX + 'early return\n' + SUFFIX + 'done\n'),
    ('throw\n', 0, PREFIX + SUFFIX + 'caught stop\ndone\n'),
    ('unknown\n', 1, ''),
    ('', 1, ''),
]


def run(command, **kwargs):
    return subprocess.run(list(map(str, command)), capture_output=True,
                          text=True, timeout=45, **kwargs)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=HERE / 'validation.json')
    args = parser.parse_args()
    report = {
        'status': 'running', 'passed': False,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'scope': '14 edited text steps; 11 complete lesson programs plus author contract checks',
        'standards': ['c++17', 'c++20'],
        'counts': {'compilations': 0, 'runtime_cases': 0, 'expected_compile_failures': 0},
        'checks': [],
    }
    try:
        journal = json.loads((PACKAGE / 'changes_t5b.json').read_text())
        assert len(journal) == 14 and len({r['step_id'] for r in journal}) == 14
        for item in journal:
            baseline = PACKAGE / 'baseline' / item['path']
            if not baseline.exists():
                baseline = ROOT / 'courses/86957' / item['path']
            before = json.loads(baseline.read_text())
            after = json.loads((PACKAGE / item['path']).read_text())
            assert before['block']['name'] == after['block']['name'] == 'text'
            assert before['block']['text'] != after['block']['text']
            before['block']['text'] = after['block']['text']
            assert before == after, ('field outside block.text', item['step_id'])

        for name, (sid, indexes) in BINDINGS.items():
            path = next((PACKAGE / 'steps').glob(f'*/*_{sid}_text.step'))
            blocks = Codes()
            blocks.feed(json.loads(path.read_text())['block']['text'])
            exact = '\n\n'.join(blocks.codes[i].rstrip() for i in indexes) + '\n'
            assert exact == (HERE / name).read_text(), ('HTML/source mismatch', name)

        inputs = [PACKAGE / row['path'] for row in journal]
        inputs += [PACKAGE / 'changes_t5b.json', Path(__file__), HERE / 'ownership_contracts.inc']
        inputs += list(HERE.glob('*.cpp'))
        report['input_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in sorted(inputs)}
        report['compiler'] = run(['g++', '--version']).stdout.splitlines()[0]
        report['platform'] = platform.platform()
        with tempfile.TemporaryDirectory(prefix='theory-t5b-') as temp:
            folder = Path(temp)
            contracts = folder / 'ownership_contracts.cpp'
            contracts.write_text(
                (HERE / 'learning_owner.cpp').read_text().split('int main() {')[0]
                + '\n' + (HERE / 'teaching_shared.cpp').read_text().split('int main() {')[0]
                + '\n' + (HERE / 'ownership_contracts.inc').read_text())
            for standard in report['standards']:
                for source in list(sorted(HERE.glob('*.cpp'))) + [contracts]:
                    binary = folder / (standard + '-' + source.stem)
                    command = ['g++', '-std=' + standard, '-Wall', '-Wextra',
                               '-Wpedantic', '-Werror', '-O1', '-g',
                               '-fsanitize=undefined', '-fno-sanitize-recover=all']
                    # Prove the distinction used by the explanation: guaranteed
                    # prvalue construction still works when optional NRVO is off.
                    if source.name in ['guaranteed_elision.cpp', 'storage_duration.cpp']:
                        command.append('-fno-elide-constructors')
                    result = run(command + [source, '-o', binary])
                    assert result.returncode == 0, (source.name, standard, result.stderr)
                    report['counts']['compilations'] += 1
                    cases = RAII_CASES if source.name == 'raii.cpp' else [('', 0, OUTPUTS[source.name])]
                    for stdin, code, expected in cases:
                        result = run([binary], input=stdin)
                        assert (result.returncode, result.stdout, result.stderr) == (code, expected, ''), (
                            source.name, standard, stdin, result.returncode, result.stdout, result.stderr)
                        report['counts']['runtime_cases'] += 1
                        report['checks'].append({'source': source.name, 'standard': standard,
                                                 'stdin': stdin, 'stdout': result.stdout,
                                                 'exit_code': result.returncode, 'passed': True})

                negatives = {
                    'copy_unique': '#include <memory>\nint main() { auto a = std::make_unique<int>(1); auto b = a; }\n',
                    'rref_from_named': 'int main() { int&& named = 7; int&& second = named; (void)second; }\n',
                    'rref_from_const': '#include <utility>\nint main() { const int n=7; int&& r = std::move(n); (void)r; }\n',
                    'named_return_immovable': (HERE / 'guaranteed_elision.cpp').read_text().replace(
                        'return Ticket{42};', 'Ticket local{42}; return local;'),
                }
                for name, content in negatives.items():
                    source = folder / (name + '.cpp')
                    source.write_text(content)
                    result = run(['g++', '-std=' + standard, '-fsyntax-only', source])
                    assert result.returncode != 0, ('negative case compiled', name, standard)
                    report['counts']['expected_compile_failures'] += 1
                    report['checks'].append({'source': name, 'standard': standard,
                                             'expected_compile_failure': True, 'passed': True})

        assert report['input_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sorted(inputs)}
        report.update(status='passed', passed=True,
                      completed_at=datetime.now(timezone.utc).isoformat(),
                      limitations=[
                          'GCC/Linux only; Windows/MSVC and macOS were not run.',
                          'UBSan used; finite checks do not prove all possible states.',
                          'No forced allocation failure or counter overflow; those boundaries are documented.',
                          'Teaching shared/weak is deliberately single-threaded; no concurrency guarantee claimed.',
                          'Existing graded steps were read for compatibility and left unchanged.',
                      ])
    except Exception as error:
        report.update(status='failed', passed=False, error=f'{type(error).__name__}: {error}')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['status', 'passed', 'counts']}, ensure_ascii=False))
    if not report['passed']:
        print(report['error'])
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
