#!/usr/bin/env python3
"""Targeted author checks for semantic LINKS corrections; never writes old reports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import json
import re
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent.parent
ROOT = PACKAGE.parents[2]
PREVIOUS = ROOT / 'improvements/86957/theory-2026-11-23/examples/t6'
REPORT = PACKAGE / 'validation/algorithms_current.json'
REPORT.parent.mkdir(parents=True, exist_ok=True)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def codes(document):
    return [html.unescape(x).strip() for x in re.findall(
        r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>',
        document['block']['text'], re.S)]

bindings = {r['step_id']: r for r in json.loads(
    (ROOT / 'courses/86957/manifest.json').read_text())['step_files']['bindings']}
inputs = set()

def effective(sid):
    path = PACKAGE / bindings[sid]['path']
    if not path.exists():
        path = ROOT / 'courses/86957' / bindings[sid]['path']
    inputs.add(path)
    return json.loads(path.read_text())

report = {
    'schema_version': 1, 'status': 'running',
    'run_started_utc': datetime.now(timezone.utc).isoformat(),
    'base_commit': '352c2796717a55f4f0db8395b7d6093d8d67c35e',
    'scope': 'LINKS algorithms: unchanged code binding, duplicate-return contracts, independent find result and file-direction transitions',
    'compilation_count': 0, 'execution_count': 0, 'checks': [],
    'standards': ['c++17', 'c++20'],
    'historical_reports_modified': False,
}
try:
    changes_path = PACKAGE / 'changes_algorithms.json'
    inputs.add(changes_path)
    changes = json.loads(changes_path.read_text())
    for row in changes:
        original_path = ROOT / 'courses/86957' / row['path']
        target_path = PACKAGE / row['path']
        inputs.update((original_path, target_path))
        before, after = json.loads(original_path.read_text()), json.loads(target_path.read_text())
        assert before['block']['name'] == after['block']['name'] == 'text'
        assert before['block']['text'] != after['block']['text']
        assert re.findall(r'<pre\b[^>]*>.*?</pre>', before['block']['text'], re.S) == re.findall(
            r'<pre\b[^>]*>.*?</pre>', after['block']['text'], re.S), row['step_id']
        before['block']['text'] = after['block']['text']
        assert before == after, row['step_id']
    report['checks'].append({'kind': 'only_block_text_and_unchanged_listings', 'steps': len(changes), 'passed': True})

    expected_headers = {
        'avl.hpp': codes(effective(3570281))[0] + '\n',
        'hash_table.hpp': codes(effective(4035481))[0] + '\n',
        'rbt.hpp': '#pragma once\n' + '\n\n'.join(
            [codes(effective(3570303))[1]] + codes(effective(3570304)) + codes(effective(3570333))) + '\n',
    }
    for name, expected in expected_headers.items():
        path = PREVIOUS / name
        inputs.add(path)
        assert path.read_text() == expected, name
    bst_code = codes(effective(3570230))[0]
    inputs.add(PREVIOUS / 'bst.cpp')
    assert (PREVIOUS / 'bst.cpp').read_text().strip() == bst_code
    prefix, delimiter, remainder = bst_code.partition('int main() {')
    assert delimiter and remainder
    report['checks'].append({'kind': 'current_html_bound_to_preserved_t6_sources',
                             'headers': sorted(expected_headers), 'bst_prefix_extracted': True,
                             'passed': True})
    expected_output = {
        'contracts.cpp': 'BST: bool; duplicates preserve values\nAVL: bool; duplicate and reinsert contracts\nRB: void; duplicate and reinsert contracts\nItemTable: returned copy survives update, rehash and erase\n',
        'stream_switching.cpp': 'output -> flush -> input: B\ninput -> position -> output; EOF recovery: AXC!\nsuccessful extraction with eofbit -> clear -> output: 17!\nempty file -> EOF recovery -> output: Q\nmissing file: opening failure\n',
    }
    report['compiler'] = subprocess.run(['g++', '--version'], capture_output=True, text=True,
                                         check=True).stdout.splitlines()[0]
    with tempfile.TemporaryDirectory(prefix='links-algorithms-', dir=ROOT.parent) as tmp_name:
        tmp = Path(tmp_name)
        (tmp / 'bst_prefix.hpp').write_text(prefix)
        for standard in report['standards']:
            for name, expected in expected_output.items():
                source = HERE / name
                inputs.add(source)
                executable = tmp / (standard + '-' + source.stem)
                command = ['g++', '-std=' + standard, '-Wall', '-Wextra', '-Wpedantic', '-Werror',
                           '-O1', '-g', '-fsanitize=undefined', '-fno-sanitize-recover=all',
                           '-I', str(PREVIOUS), '-I', str(tmp), str(source), '-o', str(executable)]
                compiled = subprocess.run(command, capture_output=True, text=True, timeout=60)
                assert compiled.returncode == 0, compiled.stderr
                report['compilation_count'] += 1
                run_dir = tmp / (standard + '-' + source.stem + '-run')
                run_dir.mkdir()
                result = subprocess.run([str(executable)], cwd=run_dir, capture_output=True,
                                        text=True, timeout=20)
                assert result.returncode == 0, result.stderr
                assert result.stdout == expected, (name, result.stdout)
                assert not result.stderr, result.stderr
                report['execution_count'] += 1
                files = {file.name: file.read_bytes().decode('ascii') for file in sorted(run_dir.glob('*.bin'))}
                if name == 'stream_switching.cpp':
                    assert files == {'empty.bin': 'Q', 'flush.bin': 'XBC', 'position.bin': 'AXC!', 'number.bin': '17!'}, files
                report['checks'].append({'source': name, 'standard': standard, 'output': result.stdout,
                                         'files': files, 'exit_code': result.returncode, 'passed': True})
    inputs.update((Path(__file__), HERE / 'README.md'))
    report['input_sha256'] = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(inputs)}
    report['status'] = 'passed'
except Exception as error:
    report['status'] = 'failed'
    report['error'] = str(error)
    raise
finally:
    report['run_finished_utc'] = datetime.now(timezone.utc).isoformat()
    report['limits'] = [
        'Linux/GCC and UBSan only; no new Windows/MSVC or macOS run.',
        'These finite checks confirm the named result contracts, not all AVL/RB states or all C++ implementations.',
        'The file checks use ordinary seekable binary files and do not model disk failure or power loss.',
        'Asymptotic costs are reasoned from code and versioned requirements, not inferred from timing.',
        'No live Stepik API reads or writes; no assessed steps or checking programs are exercised.',
    ]
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('status', 'compilation_count', 'execution_count')}))
