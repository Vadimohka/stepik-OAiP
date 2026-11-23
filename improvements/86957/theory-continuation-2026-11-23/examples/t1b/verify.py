#!/usr/bin/env python3
"""Author checks for T1B: exact lesson programs, boundaries, and staged builds.

No API writes. No learner exercises. Historical validation files are not changed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
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
BINDINGS = {
    'hello.cpp': (3173778, 0),
    'missing_definition.cpp': (3177250, 0),
    'linked_definition.cpp': (3177250, 1),
    'namespaces.cpp': (3201236, 0),
    'c_library.cpp': (3201235, 0),
    'checked_input.cpp': (3215075, 0),
    'formatting.cpp': (3215081, 0),
    'printf_example.cpp': (3215092, 0),
}
OUTPUTS = {
    'hello.cpp': 'Hello C++\n',
    'linked_definition.cpp': '',
    'namespaces.cpp': '10 20\n',
    'c_library.cpp': '7\n',
    'formatting.cpp': '7d\n125\n2.50\n0007 8\n3.6234e+01\n',
    'printf_example.cpp': '42 3.5\n',
}
INPUT_CASES = [
    ('25\n', 0, 'count: 25\n', ''),
    ('0\n', 0, 'count: 0\n', ''),
    ('1000\n', 0, 'count: 1000\n', ''),
    (' \t25\n', 0, 'count: 25\n', ''),
    ('+25\n', 0, 'count: 25\n', ''),
    ('-1\n', 1, '', 'out of range\n'),
    ('1001\n', 1, '', 'out of range\n'),
    ('abc\n', 1, '', 'input error\n'),
    ('', 1, '', 'input error\n'),
    (' \t\n', 1, '', 'input error\n'),
    ('99999999999999999999999999999999999\n', 1, '', 'input error\n'),
    ('12x\n', 0, 'count: 12\n', ''),
]


class CodeBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.language = ''
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'code' and 'class' in dict(attrs):
            self.language = dict(attrs)['class'].removeprefix('language-')
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'code' and self.current is not None:
            self.blocks.append((self.language, ''.join(self.current)))
            self.current = None


def get_blocks(path, language='cpp'):
    parser = CodeBlocks()
    parser.feed(json.loads(path.read_text())['block']['text'])
    return [code for lang, code in parser.blocks if lang == language]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, **kwargs):
    environment = os.environ.copy()
    environment['LC_ALL'] = 'C'
    return subprocess.run(list(map(str, args)), text=True, capture_output=True,
                          timeout=60, env=environment, **kwargs)


def equal(result, expected, label):
    actual = (result.returncode, result.stdout, result.stderr)
    assert actual == expected, (label, actual, expected)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path, default=HERE / 'validation.json')
    args = ap.parse_args()
    report = {
        'schema_version': 1,
        'part': 'T1B',
        'status': 'running',
        'all_passed': False,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'scope': '40 changed text payloads, seven runnable full lesson programs, one explained missing-definition source, selected fragments and mathematical explanations.',
        'standards': ['c++17', 'c++20'],
        'platform': platform.platform(),
        'counts': {'changed_payloads_checked': 0, 'source_bindings': 0,
                   'compilations': 0, 'runtime_cases': 0,
                   'expected_compile_failures': 0, 'expected_link_failures': 0,
                   'cmake_configurations': 0, 'cmake_builds': 0,
                   'mathematical_checks': 0},
        'flags': ['-Wall', '-Wextra', '-Wpedantic', '-Werror',
                  '-fsanitize=undefined', '-fno-sanitize-recover=all'],
        'runtime_cases': [],
    }

    def save():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    save()
    try:
        compiler = os.environ.get('CXX', 'g++')
        report['compiler'] = run([compiler, '--version']).stdout.splitlines()[0]
        change_path = PACKAGE / 'changes_t1b.json'
        rows = json.loads(change_path.read_text())
        assert len(rows) == 40 and len({x['step_id'] for x in rows}) == 40
        paths = {row['step_id']: PACKAGE / row['path'] for row in rows}
        historical = ROOT / 'improvements/86957/theory-2026-11-23/changes_t1.json'
        old_ids = {x['step_id'] for x in json.loads(historical.read_text())}
        assert not old_ids.intersection(paths)
        expected_ids = set()
        for lesson in [763040, 763041, 768145, 771154, 763037, 763038, 763039,
                       771155, 771156, 768140, 768146, 768143, 776128, 771009, 774618]:
            for path in (ROOT / f'courses/86957/steps/{lesson}').glob('*_text.step'):
                d = json.loads(path.read_text())
                if int(d['id']) not in old_ids:
                    expected_ids.add(int(d['id']))
        assert set(paths) == expected_ids
        for row in rows:
            new = json.loads(paths[row['step_id']].read_text())
            old = json.loads((ROOT / 'courses/86957' / row['path']).read_text())
            assert new['block']['name'] == old['block']['name'] == 'text'
            new_text = new['block']['text']
            assert new_text != old['block']['text']
            new['block']['text'] = old['block']['text']
            assert new == old, row['step_id']
            assert not re.search(r'<h[1-6][^>]*>\s*(Самостоятельно|Самопроверка|Проверьте понимание)', new_text, re.I)
            for lesson, pos in re.findall(r'https://stepik.org/lesson/(\d+)/step/(\d+)', new_text):
                assert list((ROOT / f'courses/86957/steps/{lesson}').glob(f'{int(pos):02d}_*.step'))
            report['counts']['changed_payloads_checked'] += 1
        for name, (sid, index) in BINDINGS.items():
            assert (HERE / name).read_text() == get_blocks(paths[sid])[index], name
            report['counts']['source_bindings'] += 1

        cmake_step = next((ROOT / 'courses/86957/steps').glob('*/03_3231317_text.step'))
        files = [Path(__file__), HERE / 'README.md', change_path, historical, cmake_step]
        files.extend(paths.values())
        files.extend(HERE / name for name in BINDINGS)
        input_hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
        report['input_sha256'] = input_hashes

        def maths(label, condition):
            assert condition, label
            report['counts']['mathematical_checks'] += 1

        maths('maximum normal/equal branches', [max(*x) for x in [(7, 4), (2, 9), (5, 5)]] == [7, 9, 5])
        maths('sum boundaries and table', [sum(range(1, n + 1)) for n in [0, 1, 2, 3]] == [0, 1, 3, 6])
        maths('meters conversion', Fraction('2.5') * 100 == 250 and Fraction('0.8') * 100 == 80)
        maths('integer weights', int('2C5', 16) == 709 and int('4375', 8) == 2301)
        maths('45 in three bases', int('101101', 2) == int('2D', 16) == 45)
        maths('zero representation', format(0, 'b') == '0')
        maths('exact binary fraction', Fraction(1, 2) + Fraction(1, 8) == Fraction('0.625'))
        frac = Fraction(1, 10)
        binary = ''
        for _ in range(13):
            frac *= 2
            digit = frac.numerator // frac.denominator
            binary += str(digit)
            frac -= digit
        maths('nonterminating tenth prefix', binary == '0001100110011' and frac != 0)
        exact = Fraction(3, 16) + Fraction(15, 256) + Fraction(5, 4096)
        maths('exact hex fraction', exact == Fraction('0.247314453125'))
        frac = Fraction('0.24731')
        hex_digits = ''
        for _ in range(4):
            frac *= 16
            digit = frac.numerator // frac.denominator
            hex_digits += '0123456789ABCDEF'[digit]
            frac -= digit
        maths('truncated decimal back conversion', hex_digits == '3F4F')
        scaled = Fraction('0.24731') * 4096
        maths('nearest three hex digits', (scaled + Fraction(1, 2)).numerator // (scaled + Fraction(1, 2)).denominator == 0x3F5)
        maths('endian bytes', int.from_bytes(bytes.fromhex('01 A8 CC 3D'), 'big') ==
              int.from_bytes(bytes.fromhex('3D CC A8 01'), 'little') == 27839549)
        maths('UTF8 A', 'A'.encode('utf-8') == bytes.fromhex('41'))
        maths('UTF8 Ya', 'Я'.encode('utf-8') == bytes.fromhex('D0 AF'))
        maths('UTF8 Euro', '€'.encode('utf-8') == bytes.fromhex('E2 82 AC'))

        with tempfile.TemporaryDirectory(prefix='theory-t1b-') as temp:
            folder = Path(temp)

            def compile_source(source, output, std, extra=()):
                result = run([compiler, f'-std={std}', *report['flags'], *extra, source, '-o', output])
                assert result.returncode == 0, result.stderr
                report['counts']['compilations'] += 1

            def execute(binary, expected, label, stdin=''):
                equal(run([binary], input=stdin), expected, label)
                report['counts']['runtime_cases'] += 1
                report['runtime_cases'].append(label)

            for std in report['standards']:
                for name in OUTPUTS:
                    binary = folder / f'{std}-{Path(name).stem}'
                    compile_source(HERE / name, binary, std)
                    execute(binary, (0, OUTPUTS[name], ''), f'{std}/{name}/documented-output')
                    if name == 'printf_example.cpp':
                        # Linux-only author check: force an immediate write failure.
                        stdbuf = shutil.which('stdbuf')
                        assert stdbuf and Path('/dev/full').exists(), 'Linux /dev/full and stdbuf are required for this check'
                        with open('/dev/full', 'wb') as full:
                            error = subprocess.run([stdbuf, '-o0', str(binary)], stdout=full,
                                                   stderr=subprocess.PIPE, text=True, timeout=60)
                        assert error.returncode != 0 and error.stderr == ''
                        report['counts']['runtime_cases'] += 1
                        report['runtime_cases'].append(f'{std}/{name}/immediate-output-failure')
                binary = folder / f'{std}-checked-input'
                compile_source(HERE / 'checked_input.cpp', binary, std)
                for index, (stdin, rc, stdout, stderr) in enumerate(INPUT_CASES):
                    execute(binary, (rc, stdout, stderr), f'{std}/checked-input/case-{index}:{stdin!r}', stdin)

                # The intentionally incomplete source must compile separately,
                # then fail specifically at the linking stage.
                obj = folder / f'missing-{std}.o'
                compile_source(HERE / 'missing_definition.cpp', obj, std, ['-c'])
                result = run([compiler, '-fsanitize=undefined', obj, '-o', folder / f'missing-{std}'])
                assert result.returncode != 0 and 'twice' in result.stderr, result.stderr
                report['counts']['expected_link_failures'] += 1

                # Reproduce the two-stage hello build described in the text.
                obj = folder / f'hello-{std}.o'
                result = run([compiler, f'-std={std}', '-Wall', '-Wextra', '-Wpedantic', '-c', HERE / 'hello.cpp', '-o', obj])
                assert result.returncode == 0, result.stderr
                report['counts']['compilations'] += 1
                binary = folder / f'staged-{std}'
                result = run([compiler, obj, '-o', binary])
                assert result.returncode == 0, result.stderr
                execute(binary, (0, 'Hello C++\n', ''), f'{std}/separate-object-and-link')

                # Negative cases explained by the prose, without modifying payloads.
                missing_semicolon = folder / f'syntax-{std}.cpp'
                missing_semicolon.write_text((HERE / 'hello.cpp').read_text().replace('"Hello C++\\n";', '"Hello C++\\n"'))
                ambiguous = folder / f'ambiguous-{std}.cpp'
                declarations = (HERE / 'namespaces.cpp').read_text().split('int main()')[0]
                ambiguous.write_text(declarations + 'int main() {\n' + get_blocks(paths[3201267])[0] + '}\n')
                for source, diagnostic in [(missing_semicolon, 'expected'), (ambiguous, 'ambiguous')]:
                    result = run([compiler, f'-std={std}', '-c', source, '-o', folder / 'negative.o'])
                    assert result.returncode != 0 and diagnostic in result.stderr, result.stderr
                    report['counts']['expected_compile_failures'] += 1

                # Exact fragments get only the surrounding structure they declare
                # omitted. scanf receives representable inputs only, never overflow.
                include_fragment = get_blocks(paths[3177248])[0]
                include_source = folder / f'include-{std}.cpp'
                include_source.write_text('#include <iostream>\nint main() {\n' + include_fragment.split('// В теле функции:\n')[1] + '}\n')
                binary = folder / f'include-{std}'
                compile_source(include_source, binary, std)
                execute(binary, (0, 'Hello C++\n', ''), f'{std}/include-fragment')
                scanf_source = folder / f'scanf-{std}.cpp'
                scanf_source.write_text('#include <cstdio>\nint main() {\n' + get_blocks(paths[3215092])[1] + '}\n')
                binary = folder / f'scanf-{std}'
                compile_source(scanf_source, binary, std)
                for value in ['0', '42', '-7']:
                    execute(binary, (0, value + '\n', ''), f'{std}/scanf-defined-domain/{value}', value + '\n')

            cmake = os.environ.get('CMAKE') or shutil.which('cmake')
            assert cmake, 'CMake 3.22+ is required'
            report['cmake'] = run([cmake, '--version']).stdout.splitlines()[0]
            source_dir = folder / 'cmake-source'
            source_dir.mkdir()
            (source_dir / 'main.cpp').write_text(get_blocks(cmake_step)[0])
            (source_dir / 'CMakeLists.txt').write_text(get_blocks(cmake_step, 'cmake')[0])
            for command in [[cmake, '-S', '.', '-B', 'build'], [cmake, '--build', 'build']]:
                result = run(command, cwd=source_dir)
                assert result.returncode == 0, result.stderr
            report['counts']['cmake_configurations'] += 1
            report['counts']['cmake_builds'] += 1
            execute(source_dir / 'build/hello', (0, 'Hello C++\n', ''), 'cmake/existing-full-example-with-explained-commands')

        assert input_hashes == {str(p.relative_to(ROOT)): sha(p) for p in files}
        report.update(status='passed', all_passed=True,
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      limitations=[
                          'Executed on GCC/Linux only; Windows/MSVC, macOS and alternative stream locales were not executed.',
                          'printf error path uses Linux /dev/full plus stdbuf to make the error immediate; a buffered error may be reported later in other configurations.',
                          'scanf runs only documented representable integers; undefined overflowing conversions are not executed.',
                          'No executable _start or freestanding boot illustration is provided or claimed tested.',
                          'One existing CMake example (step 3231317) is read and built without changing its payload; no claim to revalidate all old programs.',
                          'Stepik publication is not performed by this verifier.',
                      ])
        save()
        print(json.dumps({'status': report['status'], 'counts': report['counts']}, ensure_ascii=False))
        return 0
    except Exception as error:
        report.update(status='failed', all_passed=False,
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      error=f'{type(error).__name__}: {error}')
        save()
        print(report['error'])
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
