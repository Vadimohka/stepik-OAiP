#!/usr/bin/env python3
"""Verify the prepared C++ modernization package without network or Stepik access.

Run from any working directory. GCC-compatible compiler flags are intentional.
The baseline preserved by manifest.json takes precedence over the live export.
Only the final validation.json is written inside the repository; all builds,
negative controls and the Git exercise use temporary directories.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'modernization' / '86957'
FLAGS = ['-Wall', '-Wextra', '-Wpedantic', '-Werror']


class ValidationError(Exception):
    pass


class CodeBlocks(HTMLParser):
    """Extract pre/code contents, decoding HTML entities once."""
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.in_pre = False
        self.current = None
        self.blocks = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.in_pre = True
        elif tag == 'code' and self.in_pre:
            self.current = {'class': dict(attrs).get('class', ''), 'text': ''}

    def handle_endtag(self, tag):
        if tag == 'code' and self.current is not None:
            self.blocks.append(self.current)
            self.current = None
        elif tag == 'pre':
            self.in_pre = False

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data


def need(condition, message):
    if not condition:
        raise ValidationError(message)


def relative(path):
    return path.resolve().relative_to(ROOT).as_posix()


def local(path):
    value = Path(path)
    need(not value.is_absolute(), f'Expected repository-relative path: {path}')
    result = (ROOT / value).resolve()
    need(result.is_relative_to(ROOT), f'Path escapes repository: {path}')
    return result


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def block_digest(block):
    return digest(json.dumps(block, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode('utf-8'))


def normalized_code(text):
    # A surrounding line break belongs to presentation, not to the C++ program.
    return text.replace('\r\n', '\n').strip('\n')


def subprocess_result(command, *, cwd=None, data=None, env=None, timeout=60):
    return subprocess.run(command, cwd=cwd, input=data, env=env,
                          text=True, encoding='utf-8', capture_output=True,
                          timeout=timeout)


def run_ok(command, **kwargs):
    result = subprocess_result(command, **kwargs)
    need(result.returncode == 0,
         f'Command failed ({result.returncode}): {command!r}\n'
         f'{result.stdout[-3000:]}\n{result.stderr[-3000:]}')
    return result


def target_path(entry):
    return entry.get('target_path') or entry.get('revised_path') or entry.get('path')


def check_structure(report, hashes):
    manifest_path = PACKAGE / 'manifest.json'
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        need(manifest.get('course_id') == 86957, 'Unexpected course_id in manifest')
        entries = manifest.get('steps')
        need(isinstance(entries, list) and entries, 'manifest.steps is missing or empty')
        report['base_commit'] = manifest.get('base_commit')
        report['structure_source'] = relative(manifest_path)
        hashes[relative(manifest_path)] = digest(manifest_path.read_bytes())
    else:
        entries = []
        for journal in sorted(PACKAGE.glob('*_changes.json')):
            entries.extend(read_json(journal).get('changes', []))
            hashes[relative(journal)] = digest(journal.read_bytes())
        need(entries, 'No manifest or change journals found')
        report['structure_source'] = 'modernization/86957/*_changes.json'

    actual = {relative(p) for p in (PACKAGE / 'steps').glob('*/*.step')}
    listed = [target_path(e) for e in entries]
    need(all(isinstance(p, str) for p in listed), 'A changed step has no target path')
    need(len(set(listed)) == len(listed), 'Duplicate target path in package metadata')
    need(actual == set(listed),
         f'Step set differs: unlisted={sorted(actual-set(listed))}, missing={sorted(set(listed)-actual)}')
    steps = {}
    structural = []
    for entry in entries:
        target = local(target_path(entry))
        match = re.fullmatch(r'(\d+)_(\d+)_text\.step', target.name)
        need(match is not None and target.parent.name.isdigit(), f'Unexpected step name: {relative(target)}')
        position, sid = map(int, match.groups())
        lesson = int(target.parent.name)
        need(sid == int(entry['step_id']) and lesson == int(entry['lesson_id']),
             f'ID/lesson does not match path: {relative(target)}')
        if 'position' in entry:
            need(position == int(entry['position']), f'Position mismatch for step {sid}')
        need(sid not in steps, f'Duplicate step ID {sid}')
        source = local(entry['source_path'])
        need(source.name == target.name and source.parent.name == target.parent.name,
             f'Source filename/lesson mismatch for step {sid}')
        default_baseline = PACKAGE / 'baseline' / target.parent.name / target.name
        baseline = local(entry['baseline_path']) if entry.get('baseline_path') else (
            default_baseline if default_baseline.exists() else source)
        need(baseline.exists(), f'Missing baseline for step {sid}')
        before, after = read_json(baseline), read_json(target)
        need(int(before['id']) == sid == int(after['id']), f'JSON ID mismatch for step {sid}')
        need(before['block']['name'] == after['block']['name'] == 'text',
             f'Only text blocks may be changed: {sid}')
        old_text, new_text = before['block']['text'], after['block']['text']
        need(isinstance(new_text, str) and new_text.strip() and old_text != new_text,
             f'Text is empty or unchanged for step {sid}')
        expected = copy.deepcopy(before)
        expected['block']['text'] = new_text
        need(expected == after, f'Fields outside block.text changed for step {sid}')
        computed = {'before_file_sha256': digest(baseline.read_bytes()),
                    'after_file_sha256': digest(target.read_bytes()),
                    'before_block_sha256': block_digest(before['block']),
                    'after_block_sha256': block_digest(after['block'])}
        for key, value in computed.items():
            if key in entry:
                need(value == entry[key], f'{key} mismatch for step {sid}')
        hashes[relative(baseline)] = computed['before_file_sha256']
        hashes[relative(target)] = computed['after_file_sha256']
        steps[sid] = {'entry': entry, 'path': target, 'baseline': baseline,
                      'text': new_text, 'blocks': CodeBlocks(new_text).blocks}
        structural.append({'step_id': sid, 'lesson_id': lesson, 'position': position,
                           'target_path': relative(target), 'baseline_path': relative(baseline),
                           'only_block_text_changed': True})
    report['structure'] = {'passed': True, 'steps': len(steps),
                           'lessons': len({int(e['lesson_id']) for e in entries}),
                           'details': structural}
    return steps


def examples_to_check(hashes):
    examples = []
    for path in sorted((PACKAGE / 'examples').glob('*/manifest.json')):
        document = read_json(path)
        hashes[relative(path)] = digest(path.read_bytes())
        for entry in document['examples']:
            item = dict(entry)
            item.setdefault('standards', document.get('standards', ['c++17', 'c++20']))
            examples.append(item)
    containers = PACKAGE / 'containers_changes.json'
    hashes[relative(containers)] = digest(containers.read_bytes())
    for entry in read_json(containers)['examples']:
        item = dict(entry)
        item.setdefault('standards', ['c++17', 'c++20'])
        examples.append(item)
    paths = [e['path'] for e in examples]
    need(len(set(paths)) == len(paths), 'Duplicate example file in manifests')
    return examples


def check_examples(steps, compiler, temporary, report, hashes):
    examples = examples_to_check(hashes)
    results = []
    runs = builds = failures = 0
    for number, example in enumerate(examples):
        path = local(example['path'])
        sid = int(example['step_id'])
        need(sid in steps, f'Example refers to an unchanged/missing step: {sid}')
        content = path.read_text(encoding='utf-8')
        hashes[relative(path)] = digest(path.read_bytes())
        cpp = [b['text'] for b in steps[sid]['blocks']
               if any(x in b['class'].split() for x in ['language-cpp', 'language-c++'])]
        if 'code_html_index' in example:
            index = int(example['code_html_index'])
            need(0 <= index < len(cpp), f'HTML index out of range: {example["path"]}')
            cpp = [cpp[index]]
        need(normalized_code(content) in [normalized_code(x) for x in cpp],
             f'Example differs from its HTML code block: {example["path"]}')
        kind = example['kind']
        if kind == 'fragment':
            need(example.get('dependency'), f'Fragment needs an explicit dependency: {example["path"]}')
            external_validation = None
            if example.get('verification_report'):
                evidence_path = local(example['verification_report'])
                evidence = read_json(evidence_path)
                need(evidence.get('status') == 'passed', 'External dependency check did not pass')
                hashes[relative(evidence_path)] = digest(evidence_path.read_bytes())
                for name, checksum in evidence['source_sha256'].items():
                    checked = local(name)
                    need(digest(checked.read_bytes()) == checksum,
                         'External validation source has changed: '+name)
                    hashes[name] = checksum
                    if checked.name == 'CMakeLists.txt':
                        cmake_blocks = [b['text'] for b in steps[sid]['blocks']
                                        if 'language-cmake' in b['class'].split()]
                        need(normalized_code(checked.read_text(encoding='utf-8'))
                             in [normalized_code(x) for x in cmake_blocks],
                             'Dependency CMake differs from its lesson HTML')
                external_validation = {
                    'report': relative(evidence_path), 'status': evidence['status'],
                    'dependency': evidence['dependency'],
                    'tested_standards': evidence['tested_standards'],
                    'source_hashes_verified': True,
                    'execution_scope': 'Recorded real dependency run; not repeated by this offline runner'}
            results.append({'path': relative(path), 'step_id': sid, 'kind': kind,
                            'html_matches': True, 'compiled_by_this_runner': False,
                            'declared_validation_status': example.get('validation_status', 'unspecified'),
                            'external_validation': external_validation,
                            'reason': 'Dependency-specific validation is separate: '+example['dependency']})
            continue
        need(kind in ['complete', 'compile_fail'], f'Unsupported example kind: {kind}')
        standards = example['standards']
        need(standards == ['c++17', 'c++20'], f'Expected both validated standards: {example["path"]}')
        for standard in standards:
            binary = temporary / f'example-{number}-{standard}'
            result = subprocess_result([compiler, '-std='+standard, *FLAGS, str(path), '-o', str(binary)])
            builds += 1
            if kind == 'compile_fail':
                need(result.returncode > 0 and result.stderr.strip(),
                     f'Intentionally invalid example unexpectedly compiled: {example["path"]} ({standard})')
                failures += 1
                results.append({'path': relative(path), 'step_id': sid, 'standard': standard,
                                'kind': kind, 'html_matches': True, 'expected_failure_observed': True})
                continue
            need(result.returncode == 0,
                 f'Compilation failed: {example["path"]} ({standard})\n{result.stderr[-3000:]}')
            cases = example.get('cases', [])
            need(cases, f'Complete example has no execution cases: {example["path"]}')
            for index, case in enumerate(cases):
                need('expected_stdout' in case, f'Missing expected output: {example["path"]}, case {index}')
                exitcode = case.get('exitcode', case.get('expected_returncode'))
                need(isinstance(exitcode, int), f'Missing expected exit code: {example["path"]}, case {index}')
                result = subprocess_result([str(binary)], data=case.get('input', ''), timeout=10)
                need(result.returncode == exitcode and result.stdout == case['expected_stdout']
                     and result.stderr == case.get('expected_stderr', ''),
                     f'Unexpected execution result: {example["path"]} ({standard}), case {index+1}; '
                     f'exit={result.returncode}, stdout={result.stdout[:1000]!r}, stderr={result.stderr[:1000]!r}')
                runs += 1
            results.append({'path': relative(path), 'step_id': sid, 'standard': standard,
                            'kind': kind, 'html_matches': True, 'passed': True, 'cases': len(cases)})
    report['cpp_examples'] = {'passed': True, 'files': len(examples),
                             'compilation_attempts': builds, 'expected_compile_failures': failures,
                             'program_runs': runs, 'details': results}


def check_git(steps, compiler, temporary, report):
    need(3214833 in steps and 3201179 in steps, 'Git exercise or greeting step is absent')
    directory = temporary / 'git-exercise'
    directory.mkdir()
    greeting = next(b['text'] for b in steps[3201179]['blocks'] if 'language-cpp' in b['class'])
    blocks = [b['text'] for b in steps[3214833]['blocks']]
    ignore = next((b for b in blocks if '*.o' in b and 'hello' in b and 'git ' not in b), None)
    need(ignore is not None, 'The Git exercise has no .gitignore block')
    (directory / 'main.cpp').write_text(greeting, encoding='utf-8')
    (directory / '.gitignore').write_text(ignore, encoding='utf-8')
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    # No HOME changes and no global/user configuration writes.
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=str(temporary/'empty-git-config'),
               GIT_TERMINAL_PROMPT='0', GIT_PAGER='cat')
    hooks = temporary / 'empty-hooks'
    hooks.mkdir()
    git = shutil.which('git')
    need(git is not None, 'Git is required to verify the local exercise')

    def git_run(arguments):
        return run_ok([git, '-c', 'core.hooksPath='+str(hooks), '-c', 'commit.gpgsign=false', *arguments],
                      cwd=directory, env=env)

    def build_and_run(expected):
        run_ok([compiler, '-std=c++20', *FLAGS, 'main.cpp', '-o', 'hello'], cwd=directory)
        result = run_ok([str(directory/'hello')], cwd=directory)
        need(result.stdout == expected, 'Git exercise greeting does not match its expected output')

    build_and_run('Hello, C++!\n')
    commands = 0
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or not all(line.startswith('git ') for line in lines):
            continue
        for line in lines:
            parts = shlex.split(line)
            need(parts[1] in ['init', 'config', 'status', 'add', 'diff', 'commit', 'log', 'switch', 'show'],
                 'Unexpected command in the local Git exercise: '+line)
            if parts[1] == 'config':
                need(len(parts) == 4 and parts[2] in ['user.name', 'user.email'],
                     'The exercise may only set local author identity')
                parts[3] = 'Course Validator' if parts[2] == 'user.name' else 'course-validator@example.invalid'
            result = git_run(parts[1:])
            commands += 1
            if parts[1] == 'switch':
                need('Hello, C++!' in greeting, 'Greeting replacement target is missing')
                updated = greeting.replace('Hello, C++!', 'Hello, modern C++!', 1)
                (directory/'main.cpp').write_text(updated, encoding='utf-8')
                build_and_run('Hello, modern C++!\n')
            if parts[1] == 'show':
                need(result.stdout == greeting, 'Previous commit does not retain the original main.cpp')
    need(git_run(['rev-list', '--count', 'HEAD']).stdout.strip() == '2', 'Git exercise must create two commits')
    need(set(git_run(['ls-files']).stdout.splitlines()) == {'.gitignore', 'main.cpp'},
         'Generated files entered the local Git history')
    need(not git_run(['status', '--porcelain']).stdout.strip(), 'Git exercise leaves unintended changes')
    report['git_exercise'] = {'passed': True, 'commands_executed': commands,
                              'commits': 2, 'tracked_files': ['.gitignore', 'main.cpp'],
                              'user_configuration_modified': False}


def check_tooling(steps, compiler, cmake, temporary, report, hashes):
    # Run the existing checker in a minimal isolated mirror. Its baseline paths
    # therefore remain valid even after courses/ is refreshed in a later commit.
    mirror = temporary / 'tooling-repository'
    target_stage = mirror / 'modernization' / '86957'
    target_stage.mkdir(parents=True)
    journal = PACKAGE/'tooling_changes.json'
    shutil.copy2(journal, target_stage/journal.name)
    hashes[relative(journal)] = digest(journal.read_bytes())
    tooling = PACKAGE/'examples'/'tooling'
    shutil.copytree(tooling, target_stage/'examples'/'tooling')
    for path in tooling.rglob('*'):
        if path.is_file() and path.name != 'validation.json' and '__pycache__' not in path.parts:
            hashes[relative(path)] = digest(path.read_bytes())
    for entry in read_json(journal)['changes']:
        sid = int(entry['step_id'])
        for destination, source in [(entry['source_path'], steps[sid]['baseline']),
                                    (target_path(entry), steps[sid]['path'])]:
            out = mirror/destination
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, out)
    runner = target_stage/'examples'/'tooling'/'verify.py'
    result = run_ok([sys.executable, str(runner), '--cmake', cmake, '--compiler', compiler], timeout=180)
    detail = json.loads(result.stdout.strip().splitlines()[-1])
    need(detail.get('all_passed') is True, 'The CMake practice validator did not report success')
    report['tooling'] = detail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='g++', help='GCC-compatible C++ compiler')
    parser.add_argument('--cmake', default='cmake', help='CMake executable (CTest must be beside it)')
    parser.add_argument('--skip-cmake', action='store_true', help='Explicit partial check; does not produce a complete pass')
    args = parser.parse_args()
    report = {'course_id': 86957, 'status': 'running', 'all_passed': False,
              'standards': ['c++17', 'c++20'], 'flags': FLAGS,
              'scope': 'Local Linux/GCC-compatible validation; no Stepik requests or Windows/MSVC execution. Optional dependency-specific fragments have HTML checks here and separate validation evidence.'}
    hashes = {}
    temporary_path = ''
    try:
        compiler = shutil.which(args.compiler)
        need(compiler is not None, 'Compiler not found: '+Path(args.compiler).name)
        report['compiler'] = run_ok([compiler, '--version']).stdout.splitlines()[0]
        steps = check_structure(report, hashes)
        with tempfile.TemporaryDirectory(prefix='modernization-check-') as name:
            temporary_path = name
            temporary = Path(name)
            check_examples(steps, compiler, temporary, report, hashes)
            check_git(steps, compiler, temporary, report)
            if args.skip_cmake:
                report['tooling'] = {'status': 'skipped', 'reason': 'Explicit --skip-cmake'}
            else:
                cmake = shutil.which(args.cmake)
                need(cmake is not None, 'CMake not found; install it or explicitly choose --skip-cmake for partial validation')
                check_tooling(steps, compiler, cmake, temporary, report, hashes)
        report['status'] = 'partial' if args.skip_cmake else 'passed'
        report['all_passed'] = not args.skip_cmake
        report['executed_checks_passed'] = True
    except (ValidationError, OSError, ValueError, KeyError, StopIteration, subprocess.TimeoutExpired) as error:
        detail = str(error).replace(str(ROOT), '.')
        if temporary_path:
            detail = detail.replace(temporary_path, '<temporary>')
        report['status'] = 'failed'
        report['error'] = detail
    hashes[relative(Path(__file__))] = digest(Path(__file__).read_bytes())
    report['input_sha256'] = dict(sorted(hashes.items()))
    output = PACKAGE/'validation.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'all_passed': report['all_passed'],
                      'steps': report.get('structure', {}).get('steps'),
                      'program_runs': report.get('cpp_examples', {}).get('program_runs'),
                      'report': relative(output), 'error': report.get('error')}, ensure_ascii=False))
    return 1 if report['status'] == 'failed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
