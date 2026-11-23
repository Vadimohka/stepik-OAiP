#!/usr/bin/env python3
"""Author-only checks of exact T5 lesson listings; no network or Stepik writes."""
from __future__ import annotations
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent.parent
ROOT = PACKAGE.parents[2]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def blocks(text: str) -> list[str]:
    return [unescape(code).strip() for code in re.findall(r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', text, re.S)]

def execute(arguments, **kwargs):
    return subprocess.run(list(map(str, arguments)), text=True, capture_output=True, timeout=60, **kwargs)

def require(test, reason):
    if not test:
        raise AssertionError(reason)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=HERE/'validation.json', help='Use a separate path to retain an earlier receipt.')
    args = parser.parse_args()
    report = {'schema_version': 1, 'part': 'T5_modules_12_13', 'started_at': datetime.now(timezone.utc).isoformat(),
              'status': 'running', 'all_passed': False, 'standards': ['c++17', 'c++20'],
              'scope': 'Author verification of complete theory illustrations and their stated contracts; no learner tasks.',
              'counts': {'text_steps': 0, 'complete_programs': 0, 'compilations': 0, 'runtime_cases': 0,
                         'expected_compile_failures': 0, 'boundary_harness_runs': 0}, 'checks': []}
    compiler = os.environ.get('CXX', 'g++')
    try:
        journal_path = PACKAGE/'changes_t5.json'
        journal = json.loads(journal_path.read_text())
        cases = json.loads((HERE/'cases.json').read_text())
        require(len(journal) == len({row['step_id'] for row in journal}) == 45, 'Unexpected T5 membership')
        payloads = {}
        source_inputs = [journal_path, HERE/'cases.json', Path(__file__)]
        for row in journal:
            path = PACKAGE/row['path']
            baseline = PACKAGE/'baseline'/row['path']
            if not baseline.is_file():
                baseline = ROOT/'courses/86957'/row['path']
            before = json.loads(baseline.read_text())
            after = json.loads(path.read_text())
            require(before['block']['name'] == after['block']['name'] == 'text', str(row['step_id']))
            require(before['block']['text'] != after['block']['text'], 'Empty edit')
            before['block']['text'] = after['block']['text']
            require(before == after, 'Changed field outside block.text: '+str(row['step_id']))
            payloads[row['step_id']] = after
            source_inputs.append(path)
        all_complete_blocks = []
        for sid, payload in payloads.items():
            for code in blocks(payload['block']['text']):
                if re.search(r'\bint\s+main\s*\(', code):
                    all_complete_blocks.append((sid, code))
        bound_programs = []
        for case in cases:
            source = HERE/case['file']
            content = source.read_text().strip()
            require(digest(source) == case['sha256'], 'Case digest drift: '+case['file'])
            for sid in case['step_ids']:
                require(content in blocks(payloads[sid]['block']['text']), 'HTML/code mismatch: '+str(sid))
                bound_programs.append((sid, content))
        require(sorted(all_complete_blocks) == sorted(bound_programs), 'Unregistered complete lesson listing')
        require(len(cases) == 37, 'Unexpected number of complete programs')
        source_inputs += sorted(HERE.glob('*.cpp')) + sorted(HERE.glob('*.hpp'))
        report['input_sha256'] = {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(set(source_inputs))}
        report['compiler'] = execute([compiler, '--version']).stdout.splitlines()[0]
        report['counts']['text_steps'] = len(journal)
        report['counts']['complete_programs'] = len(cases)
        positive_flags = ['-Wall', '-Wextra', '-Wpedantic', '-Werror', '-O1', '-g',
                          '-fsanitize=undefined', '-fno-sanitize-recover=all']
        with tempfile.TemporaryDirectory(prefix='theory-t5-') as temp:
            folder = Path(temp)
            for standard in report['standards']:
                for case in cases:
                    binary = folder/(standard+'-'+Path(case['file']).stem)
                    compiled = execute([compiler, '-std='+standard, *positive_flags, HERE/case['file'], '-o', binary])
                    require(compiled.returncode == 0, case['file']+'\n'+compiled.stderr)
                    report['counts']['compilations'] += 1
                    inputs = case['inputs'] or [{'stdin': '', 'stdout': case['expected'], 'exit': 0}]
                    observed = []
                    for item in inputs:
                        run = execute([binary], input=item['stdin'])
                        require((run.returncode, run.stderr) == (item['exit'], ''), (case['file'], run.returncode, run.stderr))
                        if case['check']:
                            values = {key: int(value) for key, value in (line.split('=') for line in run.stdout.splitlines())}
                            if case['check'] == 'layout':
                                require(values['char'] == 1, values)
                                require(values['record'] >= values['char'] + values['int'], values)
                                require(1 <= values['value_offset'] <= values['record'] - values['int'], values)
                                require(values['record'] % values['alignment'] == 0, values)
                            elif case['check'] == 'union_size':
                                require(values['union'] >= max(values['float'], values['double']), values)
                                require(values['union'] % values['alignment'] == 0, values)
                            else:
                                raise AssertionError('Unknown semantic check: '+case['check'])
                        else:
                            require(run.stdout == item['stdout'], (case['file'], run.stdout, item['stdout']))
                        report['counts']['runtime_cases'] += 1
                        observed.append({'stdin': item['stdin'], 'stdout': run.stdout, 'exit': run.returncode})
                    report['checks'].append({'file': case['file'], 'standard': standard, 'passed': True, 'runs': observed})
                binary = folder/(standard+'-checks')
                compiled = execute([compiler, '-std='+standard, *positive_flags, HERE/'checks.cpp', '-o', binary])
                require(compiled.returncode == 0, compiled.stderr)
                report['counts']['compilations'] += 1
                run = execute([binary])
                require((run.returncode, run.stdout, run.stderr) == (0, 'T5 boundaries passed\n', ''), (run.stdout, run.stderr))
                report['counts']['runtime_cases'] += 1
                report['counts']['boundary_harness_runs'] += 1
                report['checks'].append({'file': 'checks.cpp', 'standard': standard, 'passed': True,
                                         'coverage': ['Distance constructor boundaries, carry, limit, ordering, self-add and unchanged error state',
                                                      'Counter return types, prefix/postfix maximum refusal',
                                                      'Level allowed and denied changes', 'Card rank/suit and independent copy',
                                                      'CheckedArray const return types, bounds and unchanged error state',
                                                      'Rectangle range/area and virtual destruction', 'nested trivial union active members']})
                negative_cases = {
                    'const_increment': ('#include "counter.hpp"\nint main() { const Counter x; ++x; }\n', ['const', 'qualifier']),
                    'private_member': ('#define main example_main\n#include "level.cpp"\n#undef main\nint main() { Level x; return x.value_; }\n', ['private']),
                    'const_index': ('#define main example_main\n#include "checked_array.cpp"\n#undef main\nint main() { const CheckedArray x; x[0] = 7; }\n', ['read-only', 'const']),
                    'abstract_object': ('#define main example_main\n#include "abstract.cpp"\n#undef main\nint main() { Shape x; }\n', ['abstract']),
                    'distinct_types': ('struct Point { int x, y; };\nstruct Apex { int a, b; };\nint main() { Point p{}; Apex a = p; return a.a; }\n', ['conversion']),
                }
                for name, (source, markers) in negative_cases.items():
                    path = folder/(name+'.cpp'); path.write_text(source)
                    result = execute([compiler, '-std='+standard, '-I', HERE, '-fsyntax-only', path])
                    require(result.returncode != 0 and any(marker in result.stderr for marker in markers), (name, result.stderr))
                    report['counts']['expected_compile_failures'] += 1
                    report['checks'].append({'kind': 'expected_compile_failure', 'name': name, 'standard': standard, 'passed': True})
        require(report['input_sha256'] == {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(set(source_inputs))}, 'Input changed during verification')
        report.update(status='passed', all_passed=True, limitations=[
            'Only the 37 complete changed T5 listings, their listed instructor boundary harness and five explained negative compilation cases are checked.',
            'Finite behavioral cases do not prove correctness for every program state. GCC/Linux was used; Windows/MSVC and macOS were not run.',
            'Layout and union sizes are checked using standard constraints; exact ABI numbers are observations, not portable expected outputs.',
            'No learner submissions, grading settings, videos or Stepik APIs are accessed.'])
        result_code = 0
    except Exception as error:
        report.update(status='failed', all_passed=False, error=f'{type(error).__name__}: {error}')
        result_code = 1
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ['status', 'counts']} | ({'error': report['error']} if 'error' in report else {}), ensure_ascii=False))
    return result_code

if __name__ == '__main__':
    raise SystemExit(main())
