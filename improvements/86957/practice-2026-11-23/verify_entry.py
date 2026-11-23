#!/usr/bin/env python3
"""Verify the C++ entry-task change locally, retaining all nine original tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
RELATIVE = Path('steps/763630/09_4643238_code.step')
REPORT = PACKAGE / 'validation_entry.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_report(report):
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


def input_hashes():
    paths = [PACKAGE / RELATIVE, PACKAGE / 'baseline' / RELATIVE,
             ROOT / 'courses/86957' / RELATIVE,
             PACKAGE / 'changes_entry.json', PACKAGE / 'examples/expression_identity.cpp',
             Path(__file__).resolve()]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def run(command, **kwargs):
    result = subprocess.run(command, text=True, capture_output=True, timeout=30, **kwargs)
    require(result.returncode == 0,
            f'Command failed: {command[0]}: {result.stderr[-3000:]}')
    return result


def main():
    report = {'status': 'running', 'all_passed': False, 'step_id': 4643238,
              'scope': 'Local templates, preserved grader data, and reference outputs; no live Stepik calls.'}
    write_report(report)
    try:
        initial = input_hashes()
        report['input_sha256'] = initial
        before = json.loads((PACKAGE / 'baseline' / RELATIVE).read_text())
        after = json.loads((PACKAGE / RELATIVE).read_text())
        old, new = before['block'], after['block']
        # Verify the entire object after removing only the intended additions.
        restored = copy.deepcopy(after)
        restored['block']['text'] = old['text']
        restored['block']['source']['templates_data'] = old['source']['templates_data']
        for name in ('limits', 'code_templates', 'code_templates_header_lines_count',
                     'code_templates_footer_lines_count'):
            require(set(new['options'][name]) == {'c', 'c++'}, f'Unexpected {name} languages')
            del restored['block']['options'][name]['c++']
        require(restored == before, 'Unexpected change outside text and C++ language enablement')
        require(new['options']['limits']['c++'] == old['options']['limits']['c'], 'Changed limits')
        require(new['options']['code_templates_header_lines_count']['c++'] == 0
                and new['options']['code_templates_footer_lines_count']['c++'] == 0,
                'Unexpected C++ header/footer')
        chunks = re.split(r'^::(c|c\+\+)\s*$', new['source']['templates_data'], flags=re.M)
        require(not chunks[0].strip() and len(chunks) == 5, 'Unexpected language-template syntax')
        parsed = {chunks[i]: chunks[i + 1].strip() for i in (1, 3)}
        require(parsed == new['options']['code_templates'], 'Source/options template disagreement')
        cases = new['source']['test_cases']
        require(len(cases) == 9 and all(clue.strip() == '0' for _, clue in cases),
                'Unexpected original tests')
        require(new['options']['samples'] == cases[:new['source']['samples_count']],
                'Sample mismatch')
        grader = {}
        exec(compile(new['source']['code'], '<preserved-entry-grader>', 'exec'), grader)
        require(grader['generate']() == [], 'Original entry generator changed')
        for _, clue in cases:
            require(grader['check']('0\n', clue), 'Correct output rejected')
            for wrong in ('', '1', '-1', 'nan', 'inf', '0.0', 'answer: 0'):
                require(not grader['check'](wrong, clue), 'Incorrect output accepted')
        report['compiler'] = run(['g++', '--version']).stdout.splitlines()[0]
        compilations, runtime_cases = 0, 0
        with tempfile.TemporaryDirectory(prefix='entry-course-') as directory:
            temporary = Path(directory)
            for language, suffix, compiler, standards in (
                    ('c', '.c', 'gcc', ('c99',)), ('c++', '.cpp', 'g++', ('c++17', 'c++20'))):
                template = temporary / ('template' + suffix)
                template.write_text(parsed[language])
                for standard in standards:
                    run([compiler, f'-std={standard}', '-Wall', '-Wextra', '-Wpedantic',
                         '-Werror', str(template), '-o', str(temporary / 'template')])
                    compilations += 1
            for standard in ('c++17', 'c++20'):
                binary = temporary / standard
                run(['g++', f'-std={standard}', '-O2', '-Wall', '-Wextra', '-Wpedantic',
                     '-Wconversion', '-Wsign-conversion', '-Werror',
                     str(PACKAGE / 'examples/expression_identity.cpp'), '-o', str(binary)])
                compilations += 1
                for dataset, clue in cases:
                    result = run([str(binary)], input=dataset)
                    require(result.stdout == '0\n' and not result.stderr, 'Reference output differs')
                    require(grader['check'](result.stdout, clue), 'Reference rejected')
                    runtime_cases += 1
        require(input_hashes() == initial, 'Inputs changed during verification')
        report.update(status='passed', all_passed=True, compilations=compilations,
                      runtime_cases=runtime_cases, original_test_cases=len(cases),
                      checker_negative_probes=len(cases) * 7,
                      maximum_input_characters=max(len(dataset) for dataset, _ in cases),
                      tests_and_grader_preserved=True,
                      live_stepik_verified=False)
        write_report(report)
        print(f'Entry task passed: {compilations} compilations; {runtime_cases} reference runs.')
        return 0
    except Exception as error:
        report.update(status='failed', all_passed=False, error=f'{type(error).__name__}: {error}')
        write_report(report)
        print(report['error'])
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
