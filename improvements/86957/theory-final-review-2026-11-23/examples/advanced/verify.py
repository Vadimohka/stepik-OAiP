#!/usr/bin/env python3
"""Verify current RB prose traces against the unchanged saved implementation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import platform
import re
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
ROOT = PACKAGE.parents[2]
FLAGS = ['-Wall', '-Wextra', '-Wpedantic', '-Werror', '-O1', '-g',
         '-fsanitize=undefined', '-fno-sanitize-recover=all']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocks(path):
    body = json.loads(path.read_text())['block']['text']
    return [html.unescape(code).strip() for code in re.findall(
        r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', body, re.S)]


def instrument(source):
    # These statements observe only: no lesson statement or condition changes.
    additions = []

    def insert(anchor, observation, before=False):
        nonlocal source
        assert source.count(anchor) == 1, anchor
        line = f'    advanced_trace::observe("{observation}", node, root);\n'
        source = source.replace(anchor, line + anchor if before else anchor + line)
        additions.append(line)

    insert('void RBT<T, T1>::InsCase2(shared_ptr<Node> node) {\n', 'insert_case2')
    # Here the next current node is g; retain the original local names.
    line = '        advanced_trace::observe("insert_case3_up", g, root);\n'
    anchor = '        InsCase1(g);\n'
    assert source.count(anchor) == 1
    source = source.replace(anchor, line + anchor)
    additions.append(line)
    insert('void RBT<T, T1>::DelCase5(shared_ptr<Node> node) {\n', 'delete_case5_before')
    insert('    DelCase6(node);\n', 'delete_case5_after', before=True)
    insert('void RBT<T, T1>::DelCase6(shared_ptr<Node> node) {\n', 'delete_case6_before')
    anchor = '        RotateRight(p);\n    }\n}\n'
    assert source.count(anchor) == 1
    line = '    advanced_trace::observe("delete_case6_after", node, root);\n'
    source = source.replace(anchor, '        RotateRight(p);\n    }\n' + line + '}\n')
    additions.append(line)
    return source, additions


EXPECTED = {
    'insertion': 'insert_case2(0,parent=1:red)\n'
                 'insert_case3_up(5,children=1:black,7:black)\n'
                 'insert_case2(5,parent=10:black)\n'
                 'root-to-NIL black counts: before=3, recolor=3, after=3\n',
    'deletion-left': 'delete-left: 5\n'
                     'before deletion: branch counts=2/2\n'
                     'case5 before/after: branch counts=1/2 -> 1/2\n'
                     'case6: conceptual root-to-NIL counts=3\n'
                     'case6: attached-placeholder counts=3,4\n'
                     'after detach: root-to-NIL counts=3\n',
    'deletion-right': 'delete-right: 20\n'
                      'before deletion: branch counts=2/2\n'
                      'case5 before/after: branch counts=2/1 -> 2/1\n'
                      'case6: conceptual root-to-NIL counts=3\n'
                      'case6: attached-placeholder counts=3,4\n'
                      'after detach: root-to-NIL counts=3\n',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=PACKAGE/'validation/new_advanced.json')
    args = parser.parse_args()
    report = {'schema_version': 1, 'status': 'running', 'passed': False,
              'started_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'Three concrete author traces of the saved RB cases; no learner tasks.',
              'standards': ['c++17', 'c++20'], 'flags': FLAGS,
              'compilations': 0, 'executions': 0, 'checks': []}
    try:
        inputs_path = PACKAGE/'review_inputs.json'
        rows = json.loads(inputs_path.read_text())['steps']
        selected = [row for row in rows if 12 <= row['module_number'] <= 19]
        assert len(selected) == 91
        input_files = [inputs_path, Path(__file__), HERE/'trace_rb.cpp',
                       PACKAGE/'changes_advanced.json']
        for row in selected:
            path = ROOT/row['effective_path']
            assert digest(path) == row['file_sha256'], path
            input_files.append(path)
        journal = json.loads((PACKAGE/'changes_advanced.json').read_text())
        assert {row['step_id'] for row in journal} == {3570304, 3570333}
        current = {row['step_id']: ROOT/row['effective_path'] for row in selected}
        for row in journal:
            source = current[row['step_id']]
            target = PACKAGE/row['path']
            before, after = json.loads(source.read_text()), json.loads(target.read_text())
            assert before['block']['name'] == after['block']['name'] == 'text'
            assert before['block']['text'] != after['block']['text']
            pre = r'<pre\b[^>]*>.*?</pre>'
            assert re.findall(pre, before['block']['text'], re.S) == re.findall(
                pre, after['block']['text'], re.S), row['step_id']
            before['block']['text'] = after['block']['text']
            assert before == after, row['step_id']
            current[row['step_id']] = target
            input_files.append(target)
        header_path = ROOT/'improvements/86957/theory-2026-11-23/examples/t6/rbt.hpp'
        header = '#pragma once\n' + '\n\n'.join(
            [blocks(current[3570303])[1]] + blocks(current[3570304])
            + blocks(current[3570333])) + '\n'
        assert header == header_path.read_text(), 'Lesson/header binding drift'
        input_files.append(header_path)
        observed_header, additions = instrument(header)
        recovered = observed_header
        for line in additions:
            assert recovered.count(line) == 1
            recovered = recovered.replace(line, '')
        assert recovered == header
        report['binding'] = {
            'rbt_header_path': header_path.relative_to(ROOT).as_posix(),
            'rbt_header_sha256': digest(header_path),
            'lesson_parts': [{'step_id': 3570303, 'pre_indices': [2]},
                             {'step_id': 3570304, 'pre_indices': list(range(1, 9))},
                             {'step_id': 3570333, 'pre_indices': list(range(1, 9))}],
            'pre_index_base': 1,
            'instrumentation': 'Six read-only observations in a temporary header; removal restores exact source.',
            'added_observer_lines': additions,
            'unchanged_lesson_pre_count': 16,
        }
        report['input_sha256'] = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(input_files))}
        report['compiler'] = subprocess.check_output(['g++', '--version'], text=True).splitlines()[0]
        report['platform'] = platform.platform()
        with tempfile.TemporaryDirectory(prefix='advanced-rb-', dir=ROOT.parent) as folder:
            temp = Path(folder)
            (temp/'rbt_instrumented.hpp').write_text(observed_header)
            for standard in report['standards']:
                binary = temp/standard
                command = ['g++', '-std='+standard, *FLAGS, '-I', str(temp),
                           str(HERE/'trace_rb.cpp'), '-o', str(binary)]
                compiled = subprocess.run(command, capture_output=True, text=True, timeout=60)
                assert compiled.returncode == 0, compiled.stderr
                report['compilations'] += 1
                for mode, expected in EXPECTED.items():
                    run = subprocess.run([str(binary), mode], capture_output=True, text=True, timeout=30)
                    assert (run.returncode, run.stdout, run.stderr) == (0, expected, ''), (
                        standard, mode, run.returncode, run.stdout, run.stderr)
                    report['executions'] += 1
                    report['checks'].append({'standard': standard, 'case': mode,
                                             'stdout': run.stdout, 'passed': True})
        assert report['input_sha256'] == {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(input_files))}
        report.update(status='passed', passed=True, limitations=[
            'Three explicit traces, not a proof of all red-black update paths or all template types.',
            'Read-only instrumentation is test-only and is never added to lesson code.',
            'Physical retained leaf and conceptual NIL counts differ intentionally until unlinking.',
            'Linux/GCC C++17 and C++20 with UBSan; Windows/MSVC and macOS not run.',
            'Historical validation.json files are neither replaced nor treated as this run.',
            'No Stepik request or graded-step change.'])
    except Exception as error:
        report.update(status='failed', passed=False, error=f'{type(error).__name__}: {error}')
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ['status', 'compilations', 'executions']}
                     | ({'error': report['error']} if 'error' in report else {})))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
