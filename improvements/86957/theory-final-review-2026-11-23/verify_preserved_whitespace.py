#!/usr/bin/env python3
"""Verify the narrow whitespace exception for exact historical code copies.

No Git configuration is changed and no diagnostic is silently filtered. Both
worktree and index diffs must contain exactly the nine reviewed diagnostics.
Each affected source must equal its decoded pre in the pinned Git commit.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify():
    decision_path = PACKAGE / 'whitespace_exceptions.json'
    decision = json.loads(decision_path.read_bytes())
    assert decision['status'] == 'approved_preservation_of_exact_historical_source_bytes'
    assert len(decision['files']) == 5
    assert sum(len(row['lines']) for row in decision['files']) == 9
    expected_output = []
    for row in decision['files']:
        source = ROOT / row['path']
        data = source.read_bytes()
        assert sha(data) == row['sha256'] == row['decoded_pre_sha256']
        assert subprocess.check_output(['git', 'show', ':' + row['path']], cwd=ROOT) == data
        pinned = subprocess.check_output(
            ['git', 'show', decision['base_commit'] + ':' + row['source_step_path']], cwd=ROOT)
        assert sha(pinned) == row['source_step_sha256']
        text = json.loads(pinned)['block']['text']
        blocks = re.findall(r'<pre\b[^>]*>.*?</pre>', text, re.S)
        decoded = html.unescape(re.sub(r'<[^>]*>', '', blocks[row['pre_index']]))
        assert decoded.encode() == data, row['path']
        lines = data.decode().splitlines()
        actual_trailing = [i for i, line in enumerate(lines, 1) if line.endswith((' ', '\t'))]
        assert actual_trailing == row['lines'], row['path']
        for line in row['lines']:
            expected_output.append(f"{row['path']}:{line}: trailing whitespace.\n+{lines[line - 1]}\n")
    expected = ''.join(expected_output)
    results = []
    for staged in [False, True]:
        command = ['git', 'diff', '--no-color', '--no-ext-diff']
        if staged: command.append('--cached')
        command += ['--check', decision['base_commit'], '--']
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        assert result.returncode == 2 and result.stderr == '' and result.stdout == expected, (
            'Unexpected whitespace finding; the exception cannot cover it', command,
            result.returncode, result.stdout, result.stderr)
        results.append({'command': command, 'raw_exit_code': result.returncode,
                        'diagnostics_match_exact_approved_list': True,
                        'diagnostics_sha256': sha(result.stdout.encode())})
    return {'schema_version': 1, 'status': 'passed_with_exact_historical_source_exception',
            'base_commit': decision['base_commit'], 'approved_files': 5, 'approved_lines': 9,
            'source_copies_equal_pinned_decoded_pre': True,
            'all_other_whitespace_findings': [], 'git_configuration_modified': False,
            'checks': results,
            'input_sha256': {
                str(decision_path.relative_to(ROOT)): sha(decision_path.read_bytes()),
                str(Path(__file__).resolve().relative_to(ROOT)): sha(Path(__file__).read_bytes()),
                **{r['path']: r['sha256'] for r in decision['files']}},
            'limits': ['This is a format-only exception for five immutable, exact code copies; no compiler or theory check is waived.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = verify()
    report = PACKAGE / 'validation/preserved_whitespace.json'
    if args.check:
        assert json.loads(report.read_bytes()) == result, 'Stale whitespace preservation report'
    else:
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'approved_files', 'approved_lines',
                                           'source_copies_equal_pinned_decoded_pre']}))


if __name__ == '__main__':
    main()
