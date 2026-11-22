import concurrent.futures
import argparse
import html
import itertools
import json
import re
import shutil
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--repo-root', type=Path, default=None)
parser.add_argument('--work-dir', type=Path, default=Path(__file__).resolve().parent)
args = parser.parse_args()
if args.repo_root is None:
    candidates = [Path.cwd(), *Path.cwd().parents,
                  Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    args.repo_root = next((p for p in candidates if (p / 'courses/86957/course.json').is_file()), None)
    if args.repo_root is None:
        parser.error('Cannot find courses/86957 among parent directories; pass --repo-root.')
ROOT = args.repo_root.resolve()
WORK = args.work_dir.resolve()
CHECKS = WORK / 'foundations_checks'
CHECKS.mkdir(parents=True, exist_ok=True)
baseline_path = WORK / 'foundations_baseline.json'
if baseline_path.exists():
    baseline = json.loads(baseline_path.read_text())
else:
    # The original import wrappers all use this export timestamp. The unmodified
    # source bundle provides their blocks; revised .step files provide only paths.
    bundle = json.loads((ROOT / 'courses/86957/course.json').read_text())
    paths = {int(p.name.split('_')[1]): p for p in (ROOT / 'courses/86957/steps').rglob('*.step')}
    baseline = {
        str(s['id']): {
            'path': str(paths[s['id']].relative_to(ROOT)),
            'data': {'block': s['block'], 'id': str(s['id']), 'time': '2026-11-22T18:35:40Z'}
        }
        for s in bundle['step_sources'] if s['id'] in paths
    }
changes_path = WORK / 'foundations_changes.json'
if changes_path.exists():
    changes = json.loads(changes_path.read_text())
else:
    merged = json.loads((ROOT / 'imports/86957/changes.json').read_text())
    rows = merged if isinstance(merged, list) else merged['findings']
    excluded = {28, 29, 30, 36, 37, 38}  # separately validated by the lead reviewer
    changes = []
    for row in rows:
        match = re.fullmatch(r'OAIP-?(\d+)', row['finding_id'])
        if match and 1 <= int(match[1]) <= 47 and int(match[1]) not in excluded:
            changes.append(row)
    assert len(changes) == 41, ('Expected 41 foundations changes', len(changes))
changed_ids = {sid for row in changes for sid in row['changed_step_ids']}
data = {sid: json.loads((ROOT / baseline[str(sid)]['path']).read_text()) for sid in changed_ids}
results = {'structural': {}, 'compile': [], 'executions': [], 'choices': {}, 'version_sensitive_checks': [], 'graders': {}, 'armstrong': {}}

for sid, step in data.items():
    original = baseline[str(sid)]['data']
    assert step['id'] == original['id'] and step['time'] == original['time']
    assert step['block']['name'] == original['block']['name']
    assert set(step) == set(original)
    if step['block']['name'] == 'choice':
        s = step['block']['source']
        assert s['is_multiple_choice'] == step['block']['options']['is_multiple_choice']
        assert s['sample_size'] == len(s['options'])
        n = sum(x['is_correct'] for x in s['options'])
        assert n >= 1 and (s['is_multiple_choice'] or n == 1)
results['structural'] = {'changed_steps': len(data), 'findings': len(changes), 'id_time_type_preserved': True, 'choice_settings_consistent': True}

# Compile only complete main programs that were read during editing.
compile_ids = [3201305, 3201236, 3201235, 3215075, 3231317, 3177280, 3177281, 3177283, 3177292, 3177789, 3177547, 3177546, 3177566]
jobs = []
for sid in compile_ids:
    blocks = re.findall(r'<pre><code(?:\s[^>]*)?>(.*?)</code></pre>', data[sid]['block']['text'], re.S)
    for i, text in enumerate(blocks):
        source = html.unescape(text)
        if not re.search(r'\bint\s+main\s*\(', source):
            continue
        path = CHECKS / f'{sid}_{i}.cpp'
        path.write_text(source + '\n')
        jobs.append((sid, i, path))

def compile_one(job):
    sid, i, path = job
    exe = path.with_suffix('')
    command = ['g++', '-std=c++20', '-Wall', '-Wextra', '-pedantic-errors', str(path), '-o', str(exe)]
    p = subprocess.run(command, capture_output=True, text=True, timeout=30)
    return {'step_id': sid, 'block_index': i, 'source': str(path), 'command': command, 'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results['compile'] = list(pool.map(compile_one, jobs))

# Compile-time assertions exercise the exact, explicitly chosen C++20 conditions.
assertions = r'''#include <climits>
#include <iostream>
static_assert(CHAR_BIT == 8);
static_assert(static_cast<signed char>(256L) == 0);
static_assert(static_cast<signed char>(0b11111111) == -1);
static_assert(double(3/2) == 1.0);
static_assert((double)(int)(double)3/2 == 1.5);
static_assert('1' == 49); // the quiz explicitly assumes ASCII-compatible encoding
static_assert('1' - 49 == 0);
static_assert(1 + true == 2);
static_assert(1 + bool(255) == 2);
int main() {
    unsigned char a=255; ++a;
    if(a != 0) return 1;
    int x=3; int p=++x;
    if(p != 4 || x != 4) return 2;
    x=3; int q=x++;
    if(q != 3 || x != 4) return 3;
    int z=1; switch(z) case 1: ++z; switch(z);
    return 0;
}'''
ap = CHECKS / 'choice_semantics.cpp'
ap.write_text(assertions)
ar = compile_one((0, 0, ap))
assert ar['exit_code'] == 0, ar
run = subprocess.run([str(ap.with_suffix(''))], capture_output=True, text=True, timeout=5)
assert run.returncode == 0
results['choices'] = {'compile': ar, 'exit_code': run.returncode, 'covered_findings': ['OAIP-031', 'OAIP-033', 'OAIP-034', 'OAIP-042', 'OAIP-047']}

for name, standard, source, expected_success in [
    ('wide_output_cpp17', 'c++17', '#include <iostream>\nint main(){ std::cout << wchar_t(119); }\n', True),
    ('wide_output_cpp20', 'c++20', '#include <iostream>\nint main(){ std::cout << wchar_t(119); }\n', False),
    ('wide_explicit_numeric', 'c++20', "#include <iostream>\nint main(){ wchar_t c=L'e'; std::cout << static_cast<unsigned long long>(c); }\n", True),
    ('long_float_invalid', 'c++20', 'int main(){long float value=1;}\n', False),
]:
    source_path = CHECKS / (name + '.cpp')
    source_path.write_text(source)
    command = ['g++', '-std='+standard, '-pedantic-errors', '-fsyntax-only', str(source_path)]
    p = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert (p.returncode == 0) == expected_success, (name, p.stderr)
    results['version_sensitive_checks'].append({'name': name, 'standard': standard, 'command': command, 'expected_success': expected_success, 'exit_code': p.returncode, 'stderr': p.stderr, 'passed': True})

def run_example(sid, index, input_text, expected):
    path = CHECKS / f'{sid}_{index}'
    p = subprocess.run([str(path)], input=input_text, text=True, capture_output=True, timeout=5)
    ok = p.returncode == 0 and p.stdout == expected
    results['executions'].append({'step_id': sid, 'block_index': index, 'input': input_text, 'expected': expected, 'stdout': p.stdout, 'exit_code': p.returncode, 'passed': ok})
    assert ok, results['executions'][-1]

if not any(x['exit_code'] for x in results['compile']):
    run_example(3177292, 1, '', 'x is greater than 50\nEnd of Program\n')
    run_example(3177789, 0, '', '1\n2\n3\n')
    run_example(3177547, 0, 'a b  c\n', 'Введите строку: 3 пробелов\n')
    run_example(3177547, 0, '\n', 'Введите строку: 0 пробелов\n')
    run_example(3177281, 1, '', 'He\n')
    run_example(3177281, 2, '', 'Helo\n')

# Only newly authored, fully reviewed Python checker code is executed.
step = data[3177566]['block']
ns = {}
exec(compile(step['source']['code'], 'new_reverse_checker', 'exec'), ns)
check = ns['check']
for inp, expected in step['source']['test_cases']:
    n = int(inp)
    independent = ''.join(f'{j} * {j} = {j*j}\n' for j in reversed(range(1, n)))
    assert check(independent, expected)
    assert check('  \n' + independent.replace(' ', '   ') + '\n', expected)
    assert not check(expected + '\n0 * 0 = 0', expected)
    assert not check(expected.replace(' = ', ' + ', 1), expected)
assert not check(step['source']['test_cases'][0][1], step['source']['test_cases'][1][1])
assert step['options']['samples'] == step['source']['test_cases'][:step['source']['samples_count']]
assert step['options']['code_templates']['c++'] == step['source']['templates_data'].split('::c++\n\n', 1)[1].strip()
results['graders']['3177566'] = {'datasets': len(step['source']['test_cases']), 'valid_and_whitespace_variants_pass': True, 'wrong_content_extra_tokens_and_constant_output_fail': True, 'templates_and_samples_synchronised': True}

# Enumerate digit multisets rather than scanning ten million integers.
armstrong = set()
for digits in range(1, 9):
    for values in itertools.combinations_with_replacement(range(10), digits):
        number = sum(x**digits for x in values)
        text = str(number)
        if number > 0 and len(text) == digits and tuple(sorted(map(int, text))) == values:
            armstrong.add(number)
arm = data[3299645]['block']
for inp, expected in arm['source']['test_cases']:
    actual = '\n'.join(map(str, sorted(x for x in armstrong if x < int(inp))))
    assert actual == expected, (inp, actual, expected)
assert arm['options']['samples'] == arm['source']['test_cases'][:arm['source']['samples_count']]
results['armstrong'] = {'datasets': len(arm['source']['test_cases']), 'complete_reference_by_digit_multisets': True}

(WORK / 'foundations_validation.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'compiled_programs': len(results['compile']), 'compile_failures': [x for x in results['compile'] if x['exit_code']], 'safe_runs': len(results['executions']), 'version_sensitive_checks_passed': len(results['version_sensitive_checks']), 'structural': results['structural'], 'grader_checks': results['graders'], 'armstrong': results['armstrong']}, ensure_ascii=False))
if any(x['exit_code'] for x in results['compile']):
    raise SystemExit(1)
