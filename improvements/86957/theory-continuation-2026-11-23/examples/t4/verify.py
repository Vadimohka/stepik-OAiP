#!/usr/bin/env python3
"""Verify exact T4 illustrations and their stated edge cases, without Stepik."""
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
ROOT = PKG.parents[2]
HISTORY = ROOT / 'improvements/86957/quality-2026-11-23/examples'
REPORT = HERE / 'validation.json'
FLAGS = ['-Wall', '-Wextra', '-Wpedantic', '-Werror', '-O1', '-g',
         '-fsanitize=undefined', '-fno-sanitize-recover=all']


class CodeBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.current = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'code' and 'language-cpp' in dict(attrs).get('class', '').split():
            self.active = True
            self.current = []

    def handle_data(self, value):
        if self.active:
            self.current.append(value)

    def handle_endtag(self, tag):
        if tag == 'code' and self.active:
            self.blocks.append(''.join(self.current).rstrip())
            self.active = False


def load_helper(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(report):
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


def main():
    report = {'schema_version': 1, 'status': 'running', 'all_passed': False,
              'started_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'Авторская проверка объясняющего кода T4; учебных заданий и отправок Stepik нет.',
              'standards': ['c++17', 'c++20'], 'flags': FLAGS,
              'compilations': 0, 'executions': 0, 'text_steps': 33,
              'results': [], 'limitations': [
                  'Linux/GCC; Windows/MSVC и macOS не запускались.',
                  'Отказы диска и отключение питания не моделировались.',
                  'Математические оценки не выводятся из длительности авторских запусков.']}
    save(report)
    try:
        algorithms = load_helper('historical_algorithm_cases', HISTORY / 'algorithms/verify.py')
        files = load_helper('historical_file_cases', HISTORY / 'files/verify.py')
        journal = json.loads((PKG / 'changes_t4.json').read_text())
        steps = {}
        for row in journal:
            path = PKG / row['path']
            before_path = PKG / 'baseline' / row['path']
            if not before_path.exists():
                before_path = ROOT / 'courses/86957' / row['path']
            before = json.loads(before_path.read_bytes())
            after = json.loads(path.read_bytes())
            before['block']['text'] = after['block']['text']
            assert before == after, f'Non-text edit: {row["step_id"]}'
            blocks = CodeBlocks()
            blocks.feed(after['block']['text'])
            steps[row['step_id']] = blocks.blocks
        examples = []
        for group in ['algorithms', 'files', 'containers']:
            specs = json.loads((HERE / group / 'cases.json').read_text())['examples']
            for entry in specs:
                source = HERE / group / entry['source']
                assert source.read_text().rstrip() in steps[entry['step_id']], source
                cases = list(entry['cases'])
                if group == 'algorithms':
                    cases += algorithms.generated_cases(source.name)
                if source.name == 'halving.cpp':
                    cases += [{'name': f'explained-{n}', 'stdin': f'{n}\n', 'stdout': f'{count}\n'}
                              for n, count in [(31, 4), (32, 5), (1_000_000_000, 29)]]
                if source.name in ['write_report.cpp', 'append_line.cpp', 'c_write.cpp']:
                    filename = {'write_report.cpp': 'report.txt', 'append_line.cpp': 'journal.txt',
                                'c_write.cpp': 'message.txt'}[source.name]
                    cases.append({'name': 'output_path_is_directory', 'directories': [filename],
                                  'stdout': '', 'stderr': f'Cannot open {filename}\n', 'returncode': 1})
                if source.name == 'sum_numbers.cpp':
                    for value in ['1000000', '-1000000']:
                        cases.append({'name': 'maximum_count_' + value,
                                      'files': {'numbers.txt': (value + ' ') * 1_000_000},
                                      'stdout': f'1000000 {int(value) * 1_000_000}\n',
                                      'stderr': '', 'returncode': 0})
                    cases.append({'name': 'too_many_integers', 'files': {'numbers.txt': '0 ' * 1_000_001},
                                  'stdout': '', 'stderr': 'Too many integers\n', 'returncode': 3})
                    cases.append({'name': 'explained_signed_cancellation', 'files': {'numbers.txt': '-2 0 3 -1'},
                                  'stdout': '4 0\n', 'stderr': '', 'returncode': 0})
                examples.append((source, cases))
        simple = {3213241: '5', 3213243: '1\n2\n3\n4\n5\n',
                  3213242: '1\n2\n3\n4\n5\n6\n7\n8\n9\n'}
        for sid, output in simple.items():
            source = HERE / f'{sid}.cpp'
            assert source.read_text().rstrip() in steps[sid]
            examples.append((source, [{'name': 'exact_explained_output', 'stdout': output}]))
        paths = [PKG / row['path'] for row in journal]
        paths += [PKG / 'changes_t4.json', PKG / 'review_t4.json', Path(__file__)]
        paths += [p for p in HERE.rglob('*') if p.is_file() and p.suffix in ['.cpp', '.json']
                  and p.name != 'validation.json']
        paths += [HISTORY / 'algorithms/verify.py', HISTORY / 'files/verify.py']
        report['input_sha256'] = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(paths))}
        report['compiler'] = subprocess.check_output(['g++', '--version'], text=True).splitlines()[0]
        report['platform'] = platform.platform()
        with tempfile.TemporaryDirectory(prefix='theory-t4-', dir=ROOT.parent) as folder:
            temp = Path(folder)
            fragment = temp / 'binary_format.cpp'
            assert len(steps[3215112]) == 1
            fragment.write_text('#include <fstream>\nint main() {\n' + steps[3215112][0] + '\n}\n')
            examples.append((fragment, [{'name': 'binary_mode_keeps_formatted_text', 'stdout': '',
                                        'expected_files': {'answer.dat': '42\n'}}]))
            for standard in report['standards']:
                for index, (source, cases) in enumerate(examples):
                    binary = temp / f'{standard}-{index}'
                    result = subprocess.run(['g++', f'-std={standard}', *FLAGS, str(source), '-o', str(binary)],
                                            capture_output=True, text=True, timeout=60)
                    assert result.returncode == 0, result.stderr
                    report['compilations'] += 1
                    for case in cases:
                        normalized = {'stdin': '', 'stdout': '', 'stderr': '', 'returncode': 0, **case}
                        files.check_case(binary, normalized, temp)
                        report['executions'] += 1
                    report['results'].append({'source': source.name, 'standard': standard,
                                              'cases': len(cases), 'passed': True})
        assert all(digest(ROOT / path) == expected for path, expected in report['input_sha256'].items())
        report.update(status='passed', all_passed=True,
                      finished_at=datetime.now(timezone.utc).isoformat())
        save(report)
        print(json.dumps({k: report[k] for k in ['status', 'text_steps', 'compilations', 'executions']}))
        return 0
    except Exception as error:
        report.update(status='failed', all_passed=False, error=f'{type(error).__name__}: {error}')
        save(report)
        raise


if __name__ == '__main__':
    raise SystemExit(main())
