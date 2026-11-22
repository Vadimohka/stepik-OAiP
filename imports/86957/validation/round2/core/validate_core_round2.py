#!/usr/bin/env python3
"""Read-only validation of modules 5–9, with reviewed, bounded compiler probes."""
from pathlib import Path
from html.parser import HTMLParser
import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(value).hexdigest()


def find_root():
    return next((p for p in HERE.parents if (p / 'courses/86957/steps').is_dir()), None)


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=find_root())
    parser.add_argument('--structural-only', action='store_true')
    parser.add_argument('--output', type=Path, default=HERE / 'core_validation.json')
    args = parser.parse_args()
    if args.repo is None:
        parser.error('Cannot locate courses/86957/steps; provide --repo')
    root = args.repo.resolve()
    rows = json.loads((HERE / 'core_baseline.json').read_text())
    log = json.loads((HERE / 'core.json').read_text())
    cases = json.loads((HERE / 'core_compiler_cases.json').read_text())
    checks = []
    data = {}

    def check(name, okay, **details):
        checks.append({'name': name, 'passed': bool(okay), **details})

    scope_ids = {r['id'] for r in rows}
    changed_ids = {sid for f in log['findings'] for sid in f['step_ids']}
    check('coverage', len(rows) == 150 and set(log['reviewed_step_ids']) == scope_ids,
          reviewed=len(log['reviewed_step_ids']), expected=150)
    check('unique_findings', len({f['id'] for f in log['findings']}) == len(log['findings']))
    check('changed_ids_in_scope', changed_ids <= scope_ids)
    choices = 0
    allowed_tags = {'p', 'br', 'code', 'pre', 'b', 'strong', 'i', 'em', 'u', 's', 'sup', 'sub', 'span', 'a', 'div', 'ul', 'ol', 'li', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th', 'font'}
    for r in rows:
        sid = r['id']
        path = root / r['path']
        current = json.loads(path.read_text())
        data[sid] = current
        block = current['block']
        check(f'{sid}: envelope', current['id'] == r['envelope_id'] and current['time'] == r['time'] and block['name'] == r['type'])
        if r['type'] == 'code':
            check(f'{sid}: external code ownership', sid not in changed_ids)
            continue
        actual_changed = digest(json.dumps(block, ensure_ascii=False, sort_keys=True).encode()) != r['baseline_block_sha256']
        check(f'{sid}: logged change', actual_changed == (sid in changed_ids))
        if sid in changed_ids:
            check(f'{sid}: frozen file hash', digest(path.read_bytes()) == r['expected_file_sha256'])
            for code in re.findall(r'<pre><code[^>]*>(.*?)</code></pre>', block['text'], re.S):
                check(f'{sid}: code whitespace', '\u00a0' not in html.unescape(code))
        if block['name'] == 'choice':
            choices += 1
            source = block['source']
            options = source['options']
            correct = sum(o['is_correct'] is True for o in options)
            multiple = source['is_multiple_choice']
            check(f'{sid}: choice settings', block['options']['is_multiple_choice'] == multiple and 1 <= source['sample_size'] <= len(options) and correct >= 1 and (multiple or correct == 1), true_count=correct, option_count=len(options))
            if source.get('is_html_enabled'):
                unexpected = []
                for option in options:
                    tags = Tags()
                    tags.feed(option['text'])
                    unexpected.extend(t for t in tags.tags if t not in allowed_tags)
                check(f'{sid}: HTML option text', not unexpected, unknown_tags=unexpected)

    expected = {4718310: [True, False, False, False],
                4718113: [False, False, True, False],
                4718115: [False, False, False, True],
                3426151: [True, True, True, False, True, True, False, False, False, True]}
    for sid, flags in expected.items():
        actual = [o['is_correct'] for o in data[sid]['block']['source']['options']]
        check(f'{sid}: reviewed key', actual == flags, actual=actual)
    serialized = json.dumps(data[3408968]['block']['source'], ensure_ascii=False)
    check('3408968: strpbrk answer', 'strpbrk' in serialized and 'strprbk' not in serialized)

    compiled = executed = rejected = 0
    compilers = {'cpp': shutil.which('g++'), 'c': shutil.which('gcc')}
    compiler_versions = {}
    if not args.structural_only:
        for language, compiler in compilers.items():
            check(f'{language}: compiler available', bool(compiler))
            if compiler:
                compiler_versions[language] = subprocess.run([compiler, '--version'], text=True, capture_output=True, timeout=5).stdout.splitlines()[0]
        with tempfile.TemporaryDirectory(prefix='core-round2-') as directory:
            for number, case in enumerate(cases):
                source_path = HERE / case['source']
                check(case['source'] + ': fixture hash', digest(source_path.read_bytes()) == case['source_sha256'])
                for match in case['course_blocks']:
                    code = re.findall(r'<pre><code[^>]*>(.*?)</code></pre>', data[match['step_id']]['block']['text'], re.S)[match['index']]
                    code = html.unescape(code).replace('\u00a0', ' ')
                    check(case['source'] + ': current course source', digest(code.encode()) == match['sha256'])
                compiler = compilers[case['language']]
                if not compiler:
                    continue
                binary = Path(directory) / f'case_{number}'
                command = [compiler, '-std=' + case['standard'], '-Wall', '-Wextra', '-pedantic-errors', str(source_path)]
                if case['compile_only']:
                    command += ['-fsyntax-only']
                else:
                    command += ['-o', str(binary)]
                try:
                    result = subprocess.run(command, text=True, capture_output=True, timeout=15)
                except subprocess.TimeoutExpired:
                    check(case['source'] + ': compile timeout', False)
                    continue
                compiled += 1
                if not case['expect_compile']:
                    rejected += result.returncode != 0
                diagnostic = result.stderr.replace(str(HERE) + '/', '').replace(directory, '<temporary>')
                check(case['source'] + ': ' + case['standard'] + ' compile', (result.returncode == 0) == case['expect_compile'], returncode=result.returncode, expected_success=case['expect_compile'], diagnostic=diagnostic[:1500])
                if result.returncode != 0 or case['compile_only']:
                    continue
                for run_number, run in enumerate(case['runs']):
                    try:
                        result = subprocess.run([str(binary)], input=run['input'], text=True, capture_output=True, timeout=3)
                    except subprocess.TimeoutExpired:
                        check(case['source'] + f': run {run_number}', False, error='timeout')
                        continue
                    executed += 1
                    passed = result.returncode == run['returncode']
                    if 'stdout' in run:
                        passed = passed and result.stdout == run['stdout']
                    if 'contains' in run:
                        passed = passed and all(v in result.stdout for v in run['contains'])
                    if 'stderr_contains' in run:
                        passed = passed and run['stderr_contains'] in result.stderr
                    if 'answers' in run:
                        passed = passed and [int(v) for v in re.findall(r'Answer : (\d+)', result.stdout)] == run['answers']
                    check(case['source'] + f': run {run_number}', passed, returncode=result.returncode, stdout=result.stdout[:1000], stderr=result.stderr[:500])
    report = {'scope': {'modules': [5, 6, 7, 8, 9], 'reviewed': len(rows), 'non_code': sum(r['type'] != 'code' for r in rows), 'code_owned_by_root': sum(r['type'] == 'code' for r in rows), 'changed': len(changed_ids), 'choice_steps': choices},
              'summary': {'checks': len(checks), 'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks), 'compilations': compiled, 'expected_compile_rejections': rejected, 'safe_runs': executed, 'structural_only': args.structural_only},
              'compiler_versions': compiler_versions,
              'limitations': ['No network is used by this validator.', 'Only the included reviewed probes are executed. Code tasks and checkers are not executed.', 'The billion-element new[] example is compiled with -fsyntax-only and is never run.', 'Videos and retained images were not replayed or newly rendered in this pass.', 'GCC results do not establish MSVC ABI sizes; those explanations were checked against Microsoft documentation.'],
              'checks': checks}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['summary']))
    for c in checks:
        if not c['passed']:
            print(json.dumps(c, ensure_ascii=False))
    return 1 if report['summary']['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
