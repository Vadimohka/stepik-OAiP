#!/usr/bin/env python3
"""New, isolated author checks for the second independent core review."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
ROOT = PACKAGE.parents[2]
REPORT = PACKAGE / 'validation/new_core.json'
FLAGS = ['-Wall', '-Wextra', '-Wpedantic', '-O1', '-g',
         '-fsanitize=undefined', '-fno-sanitize-recover=all']
SAMPLES = [
    (3212990, 1, 'pointer_arithmetic.cpp', '10\n20\n10\n'),
    (3212989, 1, 'pointer_to_const.cpp', None),
    (3212989, 3, 'const_view.cpp', 'value=10\nvalue=22\n'),
    (3212989, 5, 'const_pointer.cpp', 'value=10\nvalue=22\n'),
]


class PreBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.current = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.active = True
            self.current = []

    def handle_endtag(self, tag):
        if tag == 'pre' and self.active:
            self.blocks.append(''.join(self.current))
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.current.append(data)


def blocks(document):
    parser = PreBlocks()
    parser.feed(document['block']['text'])
    return parser.blocks


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    report = {
        'schema_version': 1, 'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat(),
        'base_commit': '26bbfeb5065ef3475f9ea612a3a8785f934b7c49',
        'standards': ['c++17', 'c++20'],
        'scope': 'One explanatory correction and four previously unbound full programs; author checks only.',
        'successful_compilations': 0, 'executions': 0,
        'expected_compilation_rejections': 0, 'checks': [],
        'historical_reports_modified': False,
    }
    inputs = set()
    try:
        index_path = PACKAGE / 'review_inputs.json'
        inputs.add(index_path)
        index = {r['step_id']: r for r in json.loads(index_path.read_text())['steps']}
        documents = {}
        for sid in [3177298, 3212990, 3212989, 3214873]:
            row = index[sid]
            path = ROOT / row['effective_path']
            inputs.add(path)
            assert sha(path.read_bytes()) == row['file_sha256'], sid
            doc = json.loads(path.read_text())
            assert sha(doc['block']['text'].encode()) == row['text_sha256'], sid
            documents[sid] = doc

        revision_path = PACKAGE / index[3177298]['target_relative_path']
        inputs.add(revision_path)
        revision = json.loads(revision_path.read_text())
        control = deepcopy(revision)
        control['block']['text'] = documents[3177298]['block']['text']
        assert control == documents[3177298]
        assert blocks(revision) == blocks(documents[3177298])
        array_blocks = blocks(revision)
        assert len(array_blocks) == 2
        harness = (HERE / 'array_variants.cpp').read_text()
        assert all(fragment in harness for fragment in array_blocks)
        assert 'int a[2][3]{{1, 2}, {4}};' in html.unescape(revision['block']['text'])
        assert 'int a[2][3]{{1, 2}, {4}};' in harness
        report['checks'].append({'kind': 'only_block_text_and_exact_preserved_array_fragments', 'passed': True})

        for sid, pre_index, name, _ in SAMPLES:
            path = HERE / name
            inputs.add(path)
            assert path.read_text() == blocks(documents[sid])[pre_index - 1], name
            report['checks'].append({'kind': 'exact_pre_source_binding', 'step_id': sid,
                                     'pre_index': pre_index, 'source': name, 'passed': True})

        compiler = os.environ.get('CXX', 'g++')
        assert shutil.which(compiler), f'Missing compiler: {compiler}'
        report['environment'] = {
            'platform': platform.platform(), 'python': platform.python_version(),
            'compiler': subprocess.check_output([compiler, '--version'], text=True).splitlines()[0],
            'flags': FLAGS,
        }
        negative_sources = {
            'repeated_array_definition': (
                'int main() {\n' + '\n'.join(array_blocks) + '\n}\n', r'redeclaration|redefinition'),
            'write_through_pointer_to_const': (
                'int main() { const int a = 10; const int* pa = &a;\n'
                + blocks(documents[3212989])[1] + '\n}\n', r'read-only|const'),
            'assignment_to_character_array': (
                'int main() {\n' + blocks(documents[3214873])[1] + '\n}\n',
                r'array|assignment'),
        }
        with tempfile.TemporaryDirectory(prefix='theory-final-core-', dir=ROOT.parent) as directory:
            temp = Path(directory)
            programs = [(name, expected, False) for _, _, name, expected in SAMPLES]
            programs.append(('array_variants.cpp',
                             '1 15\n74 30 3 19 0 total=126\n1 2 0 \n4 0 0 \n', True))
            for standard in report['standards']:
                for name, expected, warnings_as_errors in programs:
                    path = HERE / name
                    inputs.add(path)
                    executable = temp / (path.stem + '-' + standard)
                    command = [compiler, '-std=' + standard, *FLAGS]
                    if warnings_as_errors:
                        command += ['-Werror']
                    command += [str(path), '-o', str(executable)]
                    compiled = subprocess.run(command, text=True, capture_output=True, timeout=60)
                    assert compiled.returncode == 0, compiled.stderr
                    report['successful_compilations'] += 1
                    report['checks'].append({'kind': 'compilation', 'source': name,
                                             'standard': standard, 'warnings': compiled.stderr,
                                             'warnings_as_errors': warnings_as_errors, 'passed': True})
                    result = subprocess.run([str(executable)], text=True, capture_output=True, timeout=10)
                    assert result.returncode == 0 and result.stderr == '', result
                    if expected is None:
                        assert re.fullmatch(r'address=[^\t\r\n]+\tvalue=10\n', result.stdout), result.stdout
                        expected_description = 'Nonempty implementation-dependent address followed by value=10.'
                    else:
                        assert result.stdout == expected, (name, result.stdout, expected)
                        expected_description = expected
                    report['executions'] += 1
                    report['checks'].append({'kind': 'execution', 'source': name, 'standard': standard,
                                             'expected': expected_description, 'stdout': result.stdout,
                                             'stderr': result.stderr, 'returncode': result.returncode, 'passed': True})
                for name, (source, diagnostic) in negative_sources.items():
                    path = temp / (name + '.cpp')
                    path.write_text(source)
                    result = subprocess.run([compiler, '-std=' + standard, '-pedantic-errors',
                                             '-fsyntax-only', str(path)], text=True,
                                            capture_output=True, timeout=30)
                    assert result.returncode != 0 and re.search(diagnostic, result.stderr), result.stderr
                    report['expected_compilation_rejections'] += 1
                    report['checks'].append({'kind': 'expected_compilation_rejection', 'name': name,
                                             'standard': standard, 'source': source,
                                             'source_sha256': sha(source.encode()),
                                             'returncode': result.returncode,
                                             'diagnostic': result.stderr.replace(str(temp), '<temporary>'),
                                             'passed': True})
        inputs.update([Path(__file__), HERE / 'README.md', PACKAGE / 'changes_core.json'])
        report['input_sha256'] = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(inputs)}
        report['status'] = 'passed'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        report['limits'] = [
            'Only these five author programs and three negative constructions were compiled by this script.',
            'The four preserved programs have fixed input and no external error branches; their explained observable output is checked.',
            'const_pointer.cpp retains its historical unused-variable warning; valid C++ does not require warning-free compilation.',
            'No uninitialized int value is read; undefined behavior is not used as a negative runtime test.',
            'Pointer formatting is implementation-dependent; the expected address is not hard-coded.',
            'Linux/GCC with UBSan only; Windows/MSVC and macOS are not checked.',
            'No live Stepik access, assessed steps or learner submissions.',
        ]
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in [
        'status', 'successful_compilations', 'executions', 'expected_compilation_rejections']}))


if __name__ == '__main__':
    main()
