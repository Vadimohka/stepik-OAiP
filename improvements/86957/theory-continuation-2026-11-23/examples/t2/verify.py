#!/usr/bin/env python3
"""Author verification of exact T2 theory programs, never learner submissions."""
from __future__ import annotations
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
ROOT = PKG.parents[2]
REPORT = HERE / 'validation.json'
FLAGS = ['-Wall', '-Wextra', '-Wpedantic', '-Werror', '-O2']
FIXTURES = json.loads((HERE / 'fixtures.json').read_text())
BASE = FIXTURES['base_commit']
CPP = os.environ.get('CXX', 'g++')
CC = os.environ.get('CC', 'gcc')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def command(args, stdin='', expected=None):
    result = subprocess.run(list(map(str, args)), input=stdin, text=True,
                            capture_output=True, timeout=30)
    actual = (result.returncode, result.stdout, result.stderr)
    if expected is None:
        if result.returncode:
            raise AssertionError(f'{args}: exit {result.returncode}\n{result.stderr[-6000:]}')
    elif actual != expected:
        raise AssertionError(f'{args}: expected {expected!r}, received {actual!r}')
    return result

def code_blocks(text):
    return [html.unescape(source) for source in re.findall(
        r'<pre><code(?: class="language-[^\"]+")?>(.*?)</code></pre>', text, re.S)]

def verify_assets():
    command([sys.executable, PKG / 'authoring/t2.py', '--check'])
    changes = json.loads((PKG / 'changes_t2.json').read_text())
    review = json.loads((PKG / 'review_t2.json').read_text())
    assert len(changes) == 52
    assert set(review['changed_text_step_ids']) == {c['step_id'] for c in changes}
    existing = command(['git', '-C', ROOT, 'ls-tree', '-r', '--name-only', BASE,
                        'courses/86957/steps']).stdout.splitlines()
    targets = set()
    for filename in existing:
        path = Path(filename)
        targets.add((int(path.parent.name), int(path.name.split('_')[0])))
    all_main = {}
    links = 0
    for change in changes:
        relative = Path(change['path'])
        current = json.loads((PKG / relative).read_text())
        baseline = json.loads(command(['git', '-C', ROOT, 'show',
            f'{BASE}:courses/86957/{relative.as_posix()}']).stdout)
        assert current['block']['name'] == baseline['block']['name'] == 'text'
        assert str(current['id']) == str(change['step_id'])
        text = current['block']['text']
        assert text != baseline['block']['text']
        current['block']['text'] = baseline['block']['text']
        assert current == baseline, f'Non-text metadata changed in {relative}'
        assert not re.search(r'Самопроверка\b|Самостоятельно\b|Проверьте себя\b', text, re.I), relative
        for lesson, position in re.findall(r'https://stepik\.org/lesson/(\d+)/step/(\d+)', text):
            assert (int(lesson), int(position)) in targets, (relative, lesson, position)
            links += 1
        full = [s for s in code_blocks(text) if re.search(r'\bint\s+main\s*\(', s)]
        all_main[change['step_id']] = full
    registered = {sid: [] for sid in all_main}
    for program in FIXTURES['programs']:
        source = (HERE / program['file']).read_text()
        assert digest(HERE / program['file']) == program['source_sha256']
        assert source in all_main[program['step_id']], program['file']
        registered[program['step_id']].append(source)
    for sid in all_main:
        assert sorted(all_main[sid]) == sorted(registered[sid]), f'Unverified full program in {sid}'
    assert len(FIXTURES['programs']) == 37
    return {'changed_steps': 52, 'reviewed_steps': 63, 'preserved_steps': 11,
            'full_programs': 37, 'exact_source_matches': 37, 'internal_step_links': links}

def run_program(job):
    sample, standard, directory = job
    compiler = CC if sample['language'] == 'c' else CPP
    output = directory / (sample['file'].replace('.', '_') + '_' + standard)
    command([compiler, '-std=' + standard, *FLAGS, HERE / sample['file'], '-o', output])
    for test in sample['cases']:
        command([output], stdin=test['stdin'],
                expected=(test['returncode'], test['stdout'], test['stderr']))
    return {'file': sample['file'], 'standard': standard,
            'cases': len(sample['cases']), 'status': 'passed'}

def allocation_failure_checks(directory):
    # Wrappers are author-only: classroom C files remain byte-identical to HTML.
    checks = {
        'malloc_failure': ('c_malloc.c', '''
static void* fail_malloc(size_t bytes) { (void)bytes; return NULL; }
#define malloc fail_malloc
''', '#undef malloc\n', ''),
        'calloc_failure': ('c_realloc.c', '''
static void* fail_calloc(size_t count, size_t bytes) {
    (void)count; (void)bytes; return NULL;
}
#define calloc fail_calloc
''', '#undef calloc\n', ''),
        'realloc_failure_keeps_and_frees_old_block': ('c_realloc.c', '''
static int live_blocks = 0;
static void* track_calloc(size_t count, size_t bytes) {
    void* result = calloc(count, bytes);
    if (result != NULL) { ++live_blocks; }
    return result;
}
static void* fail_realloc(void* pointer, size_t bytes) {
    (void)pointer; (void)bytes; return NULL;
}
static void track_free(void* pointer) {
    if (pointer != NULL) { --live_blocks; }
    free(pointer);
}
#define calloc track_calloc
#define realloc fail_realloc
#define free track_free
''', '#undef calloc\n#undef realloc\n#undef free\n',
            'if (live_blocks != 0) { return 99; }')
    }
    results = []
    for name, (source, before, after, postcondition) in checks.items():
        wrapper = directory / (name + '.c')
        wrapper.write_text('#include <stdio.h>\n#include <stdlib.h>\n' + before
            + '\n#define main example_main\n#include "' + (HERE / source).as_posix()
            + '"\n#undef main\n' + after
            + '\nint main(void) { int result = example_main(); '
            + postcondition + ' return result; }\n')
        for standard in ['c11', 'c17']:
            output = directory / (name + '_' + standard)
            command([CC, '-std=' + standard, *FLAGS, wrapper, '-o', output])
            command([output], expected=(1, '', 'MEMORY\n'))
            results.append({'check': name, 'standard': standard, 'status': 'passed'})
    return results

def contract_checks(directory):
    results = []
    platform = None
    for standard in ['c++17', 'c++20']:
        output = directory / ('contracts_' + standard)
        command([CPP, '-std=' + standard, *FLAGS, HERE / 'checks/contracts.cpp', '-o', output])
        result = command([output])
        actual = json.loads(result.stdout)
        assert actual['long_long_digits'] == 63, (
            'This recorded decimal-boundary fixture set requires 63 value bits in long long; '
            'adjust expected boundary cases for a wider platform.')
        platform = actual
        results.append({'check': 'defined_boundary_contracts', 'standard': standard, 'status': 'passed'})
    rejected = {
        'narrowing': 'int main() { int value{3.5}; return value; }\n',
        'variable_length_array': 'int main(int argc, char**) { int a[argc]; a[0] = 0; return a[0]; }\n',
        'literal_without_room_for_zero': 'int main() { char text[3] = "cat"; return text[0] == \'c\' ? 0 : 1; }\n',
        'addition_of_two_literals': 'int main() { auto text = "ab" + "cd"; return text[0]; }\n'
    }
    for name, source in rejected.items():
        path = directory / (name + '.cpp')
        path.write_text(source)
        for standard in ['c++17', 'c++20']:
            result = subprocess.run([CPP, '-std=' + standard, '-pedantic-errors',
                '-fsyntax-only', str(path)], text=True, capture_output=True, timeout=30)
            assert result.returncode != 0 and result.stderr, f'{name} unexpectedly accepted in {standard}'
            results.append({'check': name, 'standard': standard, 'status': 'correctly_rejected'})
    # The same no-terminator initialization is intentionally permitted by C, not C++.
    c_path = directory / 'c_character_array.c'
    c_path.write_text('int main(void) { char text[3] = "cat"; return text[0] == \'c\' ? 0 : 1; }\n')
    for standard in ['c11', 'c17']:
        output = directory / ('c_character_array_' + standard)
        command([CC, '-std=' + standard, *FLAGS, c_path, '-o', output])
        command([output], expected=(0, '', ''))
        results.append({'check': 'C_character_array_without_terminator', 'standard': standard, 'status': 'passed'})
    return results, platform

def input_hashes():
    paths = [PKG / 'authoring/t2.py', PKG / 'changes_t2.json', PKG / 'review_t2.json']
    paths.extend(HERE / name for name in ['verify.py', 'README.md', 'fixtures.json', 'checks/contracts.cpp'])
    paths.extend(HERE / p['file'] for p in FIXTURES['programs'])
    paths.extend(PKG / c['path'] for c in json.loads((PKG / 'changes_t2.json').read_text()))
    return {path.relative_to(PKG).as_posix(): digest(path) for path in sorted(set(paths))}

def main():
    report = {'schema_version': 1, 'package': 'T2', 'base_commit': BASE,
        'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'running',
        'historical_reports_replaced': False,
        'limits': ['Linux/GCC only for this run; no Windows/MSVC or macOS execution.',
                  '37 exact full programs in 52 changed T2 steps; not all 283 course texts/programs.',
                  'Fragments without main were reviewed; only four explicit negative examples and the contract harness are compiled separately.',
                  'Real OS exhaustion is not forced; allocator-failure branches are checked by deterministic author-only substitution.',
                  'Decimal limits in parse_integer fixtures correspond to the recorded 63 value bits of long long.']}
    try:
        for compiler in [CPP, CC]:
            assert shutil.which(compiler), f'Missing compiler {compiler}'
        report['compilers'] = {name: command([name, '--version']).stdout.splitlines()[0] for name in [CPP, CC]}
        report['environment'] = {'platform': sys.platform, 'python': sys.version.split()[0], 'flags': FLAGS}
        report['assets'] = verify_assets()
        with tempfile.TemporaryDirectory(prefix='stepik_t2_') as temporary:
            directory = Path(temporary)
            contract_results, platform = contract_checks(directory)
            report['platform_types'] = platform
            report['contract_checks'] = contract_results
            jobs = [(sample, standard, directory) for sample in FIXTURES['programs']
                    for standard in (['c11', 'c17'] if sample['language'] == 'c' else ['c++17', 'c++20'])]
            with ThreadPoolExecutor(max_workers=4) as pool:
                report['programs'] = list(pool.map(run_program, jobs))
            report['allocation_failures'] = allocation_failure_checks(directory)
        report['summary'] = {'exact_programs': 37, 'cpp_programs': 35, 'c_programs': 2,
            'successful_program_compilations': len(report['programs']),
            'program_runs': sum(p['cases'] for p in report['programs']),
            'allocation_failure_runs': len(report['allocation_failures']),
            'contract_checks': len(report['contract_checks']),
            'expected_compilation_rejections': sum(c['status'] == 'correctly_rejected' for c in report['contract_checks'])}
        report['input_sha256'] = input_hashes()
        report['status'] = 'passed'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = str(error)
        raise
    finally:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': report['status'], **report['summary']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
