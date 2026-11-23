#!/usr/bin/env python3
"""Compile the exact lesson examples and check isolated file fixtures."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]


class CodeBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.capture = False
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'code' and dict(attrs).get('class') == 'language-cpp':
            self.capture = True
            self.parts = []

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'code' and self.capture:
            self.blocks.append(''.join(self.parts).rstrip())
            self.capture = False


def check_case(executable, case, temp_parent):
    with tempfile.TemporaryDirectory(dir=temp_parent) as tmp:
        work = Path(tmp)
        for name, content in case.get('files', {}).items():
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode('utf-8'))
        for name in case.get('directories', []):
            (work / name).mkdir(parents=True, exist_ok=True)
        run = subprocess.run([str(executable)], cwd=work,
                             input=case.get('stdin', ''), text=True,
                             encoding='utf-8', capture_output=True, timeout=20)
        for key in ('stdout', 'stderr', 'returncode'):
            if getattr(run, key) != case[key]:
                raise AssertionError(f'{case["name"]}: {key}: '
                                     f'{getattr(run, key)!r} != {case[key]!r}')
        for name, content in case.get('expected_files', {}).items():
            if (work / name).read_bytes() != content.encode('utf-8'):
                raise AssertionError(f'{case["name"]}: wrong contents of {name}')
        for name in case.get('expected_absent', []):
            if (work / name).exists():
                raise AssertionError(f'{case["name"]}: unexpected creation of {name}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='g++')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        args.output.write_text(json.dumps({'status': 'running', 'all_passed': False}, indent=2) + '\n',
                               encoding='utf-8')
    examples = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))['examples']
    results = []
    checksums = {}
    steps = {int(p.name.split('_')[1]): p for p in (PACKAGE / 'steps').glob('*/*.step')}
    for example in examples:
        source = HERE / example['source']
        step = steps[example['step_id']]
        blocks = CodeBlocks()
        blocks.feed(json.loads(step.read_text(encoding='utf-8'))['block']['text'])
        if source.read_text(encoding='utf-8').rstrip() not in blocks.blocks:
            raise AssertionError(f'Lesson code differs from {source.name}')
        checksums[str(source.relative_to(PACKAGE))] = hashlib.sha256(source.read_bytes()).hexdigest()
        checksums[str(step.relative_to(PACKAGE))] = hashlib.sha256(step.read_bytes()).hexdigest()
    fragment_step = steps[3215112]
    fragment_blocks = CodeBlocks()
    fragment_blocks.feed(json.loads(fragment_step.read_text(encoding='utf-8'))['block']['text'])
    if len(fragment_blocks.blocks) != 1:
        raise AssertionError('Expected exactly one binary-mode fragment')
    fragment_source = '#include <fstream>\nint main() {\n' + fragment_blocks.blocks[0] + '\n}\n'
    checksums[str(fragment_step.relative_to(PACKAGE))] = hashlib.sha256(fragment_step.read_bytes()).hexdigest()
    for extra in (HERE / 'cases.json', Path(__file__)):
        checksums[str(extra.relative_to(PACKAGE))] = hashlib.sha256(extra.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix='.file-io-check-', dir=HERE) as temp:
        root = Path(temp)
        for standard in ('c++17', 'c++20'):
            snippet = root / 'binary_text_fragment.cpp'
            snippet.write_text(fragment_source, encoding='utf-8')
            snippet_exe = root / ('binary-text-fragment-' + standard)
            compiled = subprocess.run([args.compiler, '-std=' + standard, '-Wall', '-Wextra',
                                       '-Wpedantic', '-Werror', str(snippet), '-o', str(snippet_exe)],
                                      text=True, encoding='utf-8', capture_output=True, timeout=60)
            if compiled.returncode:
                raise AssertionError(f'Binary-mode fragment: {compiled.stderr}')
            snippet_case = {'name': 'binary_mode_still_formats_text', 'stdout': '', 'stderr': '',
                            'returncode': 0, 'expected_files': {'answer.dat': '42\n'}}
            check_case(snippet_exe, snippet_case, root)
            results.append({'source': 'step:3215112/fragment', 'standard': standard,
                            'case': snippet_case['name'], 'passed': True})
            for example in examples:
                source = HERE / example['source']
                exe = root / (source.stem + '-' + standard)
                command = [args.compiler, '-std=' + standard, '-Wall', '-Wextra',
                           '-Wpedantic', '-Wconversion', '-Wsign-conversion',
                           '-Werror', str(source), '-o', str(exe)]
                compiled = subprocess.run(command, text=True, encoding='utf-8',
                                          capture_output=True, timeout=60)
                if compiled.returncode:
                    raise AssertionError(f'{source.name}: {compiled.stderr}')
                cases = list(example['cases'])
                if source.name in {'write_report.cpp', 'append_line.cpp', 'c_write.cpp'}:
                    filename = {'write_report.cpp': 'report.txt', 'append_line.cpp': 'journal.txt',
                                'c_write.cpp': 'message.txt'}[source.name]
                    cases.append({'name': 'output_path_is_directory', 'directories': [filename],
                                  'stdout': '', 'stderr': f'Cannot open {filename}\n', 'returncode': 1})
                if source.name == 'sum_numbers.cpp':
                    for value in ('1000000', '-1000000'):
                        cases.append({'name': 'maximum_count_' + value,
                                      'files': {'numbers.txt': (value + ' ') * 1_000_000},
                                      'stdout': f'1000000 {int(value) * 1_000_000}\n',
                                      'stderr': '', 'returncode': 0})
                    cases.append({'name': 'too_many_integers',
                                  'files': {'numbers.txt': '0 ' * 1_000_001},
                                  'stdout': '', 'stderr': 'Too many integers\n', 'returncode': 3})
                for case in cases:
                    check_case(exe, case, root)
                    results.append({'source': example['source'], 'standard': standard,
                                    'case': case['name'], 'passed': True})

    result = {'status': 'passed', 'all_passed': True,
              'compiler': subprocess.check_output([args.compiler, '--version'], text=True).splitlines()[0],
              'standards': ['c++17', 'c++20'], 'examples': len(examples), 'fragments': 1, 'cases': len(results),
              'checks': results, 'input_sha256': checksums,
              'limitations': ['Observed on Linux; exact file bytes and error behavior were not run on Windows.',
                              'Disk-full and hardware I/O failures are not injected by this check.']}
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'compiler', 'standards', 'examples', 'cases')}))


if __name__ == '__main__':
    main()
