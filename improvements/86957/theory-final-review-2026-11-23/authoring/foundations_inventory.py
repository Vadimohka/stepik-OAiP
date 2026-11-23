#!/usr/bin/env python3
"""Reproduce the manually classified pre-block inventory for modules 1–4."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
OLD = Path('improvements/86957/theory-2026-11-23')
CONTINUATION = Path('improvements/86957/theory-continuation-2026-11-23')

# Each positive full program is explicitly bound to one executable check.
T1_DYNAMIC = {3201305: 0, 3201179: 0, 3231317: 0}
T1B_STATIC = {
    3173778: (0, 'hello.cpp'), 3177250: (1, 'linked_definition.cpp'),
    3215075: (0, 'checked_input.cpp'), 3215081: (0, 'formatting.cpp'),
    3215092: (0, 'printf_example.cpp'), 3201236: (0, 'namespaces.cpp'),
    3201235: (0, 'c_library.cpp'),
}
T2_STATIC = {
    3177280: (1, 'objects.cpp'), 3177291: (1, 'division.cpp'),
    3177474: (0, 'checked_conversion.cpp'), 3177292: (1, 'sign.cpp'),
    3215105: (0, 'switch_command.cpp'), 3177541: (0, 'minimum.cpp'),
    3177546: (0, 'break.cpp'), 3177547: (0, 'continue.cpp'),
    3177565: (0, 'while_squares.cpp'), 3177651: (0, 'for_squares.cpp'),
    3177786: (0, 'do_while.cpp'), 3177789: (0, 'filtered_sum.cpp'),
}
NEW_STATIC = {
    (3177281, 1): 'wide_characters.cpp', (3177281, 2): 'narrow_casts.cpp',
    (3177283, 1): 'type_sizes.cpp',
}
ADDITIONAL_NEW = {(3177291, 1): 'integer_division.cpp', (3177292, 1): 'if_input.cpp'}
OUTPUT = {(3173778, 1), (3173871, 1), (3201179, 3), (3215081, 1),
          (3201236, 1), (3231317, 4)}
PSEUDOCODE = {(3173935, 0), (3173955, 0), (3173970, 0), (3237955, 0)}
MATH = {(3215255, 0), (3177283, 0)}
TEXT_COMMANDS = {(3231317, 3), (3231228, 0)}


class PreBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.language = ''
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.current = []
            self.language = ''
        if tag == 'code' and self.current is not None:
            self.language = dict(attrs).get('class', '').removeprefix('language-')

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'pre' and self.current is not None:
            self.blocks.append({'language': self.language, 'source': ''.join(self.current)})
            self.current = None


def blocks(path):
    parser = PreBlocks()
    parser.feed(json.loads(path.read_text())['block']['text'])
    return parser.blocks


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mapping(suite, code, *, static=None, dynamic=None, mode='compile_and_run'):
    base = PACKAGE if suite == 'foundations' else (OLD if suite == 't1' else CONTINUATION)
    example = base / 'examples' / suite
    if suite == 'foundations':
        report = PACKAGE / 'validation/new_foundations.json'
    else:
        report = PACKAGE / 'validation/recheck' / f'{suite}.json'
    result = {
        'suite': suite,
        'verification_mode': mode,
        'verifier_path': (example / 'verify.py').relative_to(ROOT).as_posix()
                         if example.is_absolute() else (example / 'verify.py').as_posix(),
        'current_report_path': report.relative_to(ROOT).as_posix(),
        'current_report_status': json.loads(report.read_text())['status'],
        'current_run_owner': 'verify_foundations' if suite == 'foundations' else 'root',
    }
    assert result['current_report_status'] == 'passed', report
    if static:
        path = example / static
        path = path if path.is_absolute() else ROOT / path
        source = path.read_text()
        assert source == code, (suite, static)
        result.update(source_path=path.relative_to(ROOT).as_posix(),
                      source_sha256=sha(path.read_bytes()), exact_source_match=True)
    if dynamic:
        sid, index = dynamic
        paths = list((ROOT / OLD / 'steps').glob(f'*/*_{sid}_text.step'))
        assert len(paths) == 1, sid
        path = paths[0]
        assert blocks(path)[index]['source'] == code, sid
        result['dynamic_extraction'] = {
            'source_step_path': path.relative_to(ROOT).as_posix(),
            'step_id': sid, 'pre_index': index,
            'function': 'blocks(step_id)', 'exact_source_match': True,
        }
    return result


def classify(sid, index, language, code):
    key = (sid, index)
    if key in [(3177250, 0), (3201189, 0), (3201267, 0)]:
        return 'expected_failure'
    if re.search(r'\bint\s+main\s*\(', code):
        return 'full_program'
    if key in OUTPUT:
        return 'output'
    if key in PSEUDOCODE:
        return 'pseudocode'
    if key in MATH:
        return 'mathematical_notation'
    if key == (3177292, 0):
        return 'syntax_template'
    if language in ['bash', 'powershell'] or key in TEXT_COMMANDS:
        return 'shell_commands'
    if language == 'cmake':
        return 'build_configuration'
    return 'fragment'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    input_path = PACKAGE / 'review_inputs.json'
    inputs = json.loads(input_path.read_text())
    changes = {row['step_id']: row for row in json.loads((PACKAGE / 'changes_foundations.json').read_text())}
    inventory = []
    selected = [row for row in inputs['steps'] if row['module_number'] <= 4]
    assert len(selected) == 96
    for row in selected:
        source = ROOT / row['effective_path']
        assert sha(source.read_bytes()) == row['file_sha256']
        target = PACKAGE / changes[row['step_id']]['path'] if row['step_id'] in changes else source
        current = blocks(target)
        assert current == blocks(source), row['step_id']
        for index, block in enumerate(current):
            sid, code = row['step_id'], block['source']
            key = (sid, index)
            kind = classify(sid, index, block['language'], code)
            item = {
                'step_id': sid, 'module_number': row['module_number'], 'pre_index': index,
                'kind': kind, 'language_attribute': block['language'],
                'code_sha256': sha(code.encode('utf-8')),
                'effective_path': target.relative_to(ROOT).as_posix(),
                'effective_file_sha256': sha(target.read_bytes()),
                'content_changed': False,
                'review': 'read_and_classified',
                'test_mapping': [],
            }
            if kind == 'full_program':
                item['program_form'] = 'standalone'
                if sid in T1_DYNAMIC:
                    assert index == T1_DYNAMIC[sid]
                    item['test_mapping'].append(mapping('t1', code, dynamic=key))
                elif sid in T1B_STATIC:
                    expected_index, filename = T1B_STATIC[sid]
                    assert index == expected_index
                    item['test_mapping'].append(mapping('t1b', code, static=filename))
                elif sid in T2_STATIC:
                    expected_index, filename = T2_STATIC[sid]
                    assert index == expected_index
                    item['test_mapping'].append(mapping('t2', code, static=filename))
                elif key in NEW_STATIC:
                    item['test_mapping'].append(mapping('foundations', code, static=NEW_STATIC[key]))
                else:
                    raise AssertionError(f'Full program lacks current run mapping: {key}')
                if key in ADDITIONAL_NEW:
                    item['test_mapping'].append(mapping('foundations', code, static=ADDITIONAL_NEW[key]))
            elif key == (3177250, 0):
                item['program_form'] = 'intentionally_missing_definition'
                item['expected_outcome'] = 'object_compilation_succeeds_then_link_fails_for_twice'
                item['test_mapping'].append(mapping('t1b', code, static='missing_definition.cpp',
                                                    mode='compile_object_then_expected_link_failure'))
            elif key == (3201189, 0):
                item['program_form'] = 'standalone_intentionally_ill_formed'
                item['expected_outcome'] = 'compile_failure_unqualified_cout'
                item['test_mapping'].append(mapping('t1', code, dynamic=key, mode='expected_compile_failure'))
            elif key == (3201267, 0):
                item['program_form'] = 'fragment_with_explicit_wrapper'
                item['expected_outcome'] = 'compile_failure_ambiguous_value'
                item['test_mapping'].append({
                    'suite': 't1b', 'verification_mode': 'expected_compile_failure_with_wrapper',
                    'verifier_path': (CONTINUATION / 'examples/t1b/verify.py').as_posix(),
                    'dynamic_extraction': {'step_id': sid, 'pre_index': index,
                                           'wrapper': 'namespace declarations plus int main'},
                    'current_report_path': (PACKAGE / 'validation/recheck/t1b.json').relative_to(ROOT).as_posix(),
                    'current_report_status': 'passed', 'current_run_owner': 'root',
                })
            elif key in [(3177248, 0), (3215092, 1)]:
                item['test_mapping'].append({
                    'suite': 't1b', 'verification_mode': 'compile_and_run_with_explicit_wrapper',
                    'verifier_path': (CONTINUATION / 'examples/t1b/verify.py').as_posix(),
                    'dynamic_extraction': {'step_id': sid, 'pre_index': index,
                                           'wrapper': 'include header plus int main'},
                    'current_report_path': (PACKAGE / 'validation/recheck/t1b.json').relative_to(ROOT).as_posix(),
                    'current_report_status': 'passed', 'current_run_owner': 'root',
                })
            if not item['test_mapping']:
                item['execution_claim'] = 'No individual execution claim: read as a fragment, command, notation, output or configuration.'
            if key in [(3177281, 1), (3177281, 2), (3177283, 1)]:
                item['platform_limit'] = 'Observed output is for recorded Linux/GCC and C locale; sizeof/encoding observations are not portable language guarantees.'
            if key == (3177504, 1):
                item['version_limit'] = 'The signed bitwise-not explanation is explicitly limited to C++20 in its surrounding text.'
            inventory.append(item)
    counts = dict(sorted(Counter(row['kind'] for row in inventory).items()))
    assert len(inventory) == 66 and counts['full_program'] == 25 and counts['expected_failure'] == 3
    result = {
        'schema_version': 1, 'base_commit': inputs['base_commit'],
        'review_input_path': input_path.relative_to(ROOT).as_posix(),
        'review_input_sha256': sha(input_path.read_bytes()),
        'scope': 'Every pre block in all 96 effective texts of modules 1–4; pre_index is zero-based.',
        'counts': {'reviewed_text_steps': 96, 'pre_blocks': len(inventory), **counts,
                   'standalone_positive_programs': 25,
                   'full_sources_with_expected_failure': 2,
                   'fragments_with_expected_failure': 1,
                   'newly_closed_full_program_coverage_gaps': 3},
        'coverage': 'All 25 positive full listings map to current successful C++17/C++20 runs. '
                    'Three separate expected failures are not counted as positive programs. '
                    'Fragments and commands without a mapping are not claimed executed.',
        'blocks': inventory,
    }
    target = PACKAGE / 'code_inventory_foundations.json'
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
    if args.check:
        assert target.read_bytes() == encoded, target
    else:
        target.write_bytes(encoded)
    print(json.dumps({'status': 'checked' if args.check else 'written', 'counts': result['counts']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
