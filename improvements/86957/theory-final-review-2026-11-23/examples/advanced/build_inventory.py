#!/usr/bin/env python3
"""Bind every advanced lesson pre block to explicit current source/test evidence."""
from __future__ import annotations

from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
ROOT = PACKAGE.parents[2]

SUITE_DIRS = {
    't5': 'improvements/86957/theory-continuation-2026-11-23/examples/t5',
    't5b': 'improvements/86957/theory-continuation-2026-11-23/examples/t5b',
    't6': 'improvements/86957/theory-2026-11-23/examples/t6',
    't4': 'improvements/86957/theory-continuation-2026-11-23/examples/t4',
}
HEADER_UNITS = {
    'rbt.hpp': ['rbt_demo.cpp', 'invariants.cpp'],
    'avl.hpp': ['avl_demo.cpp', 'invariants.cpp'],
    'hash_table.hpp': ['hash_demo.cpp', 'invariants.cpp'],
}


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return sha_bytes(path.read_bytes())


def decode(raw):
    return html.unescape(re.sub(r'<[^>]*>', '', raw))


def main():
    rows = json.loads((PACKAGE/'review_inputs.json').read_text())['steps']
    rows = [row for row in rows if 12 <= row['module_number'] <= 19]
    assert len(rows) == 91
    changed = {row['step_id']: PACKAGE/row['path']
               for row in json.loads((PACKAGE/'changes_advanced.json').read_text())}
    suites, source_files = {}, {}
    for name, relative in SUITE_DIRS.items():
        folder = ROOT/relative
        verifier = folder/'verify.py'
        report_path = PACKAGE/'validation/recheck'/f'{name}.json'
        report = json.loads(report_path.read_text())
        assert report['status'] == 'passed'
        assert report['input_sha256'][verifier.relative_to(ROOT).as_posix()] == sha(verifier)
        suites[name] = {
            'verifier_path': verifier.relative_to(ROOT).as_posix(),
            'verifier_sha256': sha(verifier),
            'current_report_path': report_path.relative_to(ROOT).as_posix(),
            'current_report_sha256': sha(report_path),
            'status': 'passed',
            'standards': report['standards'],
        }
        source_files[name] = [(path, path.read_text()) for path in sorted(folder.rglob('*'))
                              if path.is_file() and path.suffix in {'.cpp', '.hpp', '.inc'}]
    entries, step_index = [], []
    cpp_by_id = {}
    for row in rows:
        sid = row['step_id']
        input_path = ROOT/row['effective_path']
        assert sha(input_path) == row['file_sha256']
        path = changed.get(sid, input_path)
        body = json.loads(path.read_text())['block']['text']
        pres = list(re.finditer(r'<pre\b[^>]*>(.*?)</pre>', body, re.S))
        step_index.append({'step_id': sid, 'module_number': row['module_number'],
                           'effective_path': path.relative_to(ROOT).as_posix(),
                           'effective_file_sha256': sha(path),
                           'text_sha256': sha_bytes(body.encode()),
                           'pre_count': len(pres)})
        suite = ('t5' if row['module_number'] <= 13 else 't5b'
                 if row['module_number'] <= 15 else 't6'
                 if row['module_number'] <= 18 else 't4')
        report = json.loads((PACKAGE/'validation/recheck'/f'{suite}.json').read_text())
        prior_program_mappings = []
        cpp_by_id[sid] = []
        for index, match in enumerate(pres, 1):
            raw = match.group(1)
            code = decode(raw)
            is_cpp = bool(re.search(r'class=["\'][^"\']*language-cpp', raw))
            is_main = bool(re.search(r'\bint\s+main\s*\(', code))
            combined = sid == 3570213 and index in {1, 2}
            kind = ('fragment' if combined else 'full_program' if is_cpp and is_main
                    else 'fragment' if is_cpp else 'output')
            item = {'step_id': sid, 'pre_index': index, 'kind': kind,
                    'decoded_sha256': sha_bytes(code.encode()),
                    'raw_pre_sha256': sha_bytes(match.group(0).encode()),
                    'line_count': len(code.splitlines()), 'source_test_mapping': []}
            if is_cpp:
                cpp_by_id[sid].append(code.strip())
            if kind == 'output':
                item['data_role'] = ('sample_input' if sid in {4035311, 4035416, 4035427, 4035430}
                                     and index == 2 else 'expected_output')
                item['source_test_mapping'] = prior_program_mappings
                item['verification'] = 'data_for_previous_program' if prior_program_mappings else 'editorial_read'
            else:
                for source, content in source_files[suite]:
                    if content.strip() == code.strip():
                        relation = 'whole_file_ignoring_outer_whitespace'
                    elif combined and code.strip() in content:
                        relation = 'ordered_part_of_combined_program'
                    elif sid in {3570303, 3570304, 3570333} and source.name == 'rbt.hpp' and code.strip() in content:
                        relation = 'ordered_part_of_assembled_header'
                    else:
                        continue
                    relative = source.relative_to(ROOT).as_posix()
                    assert report['input_sha256'][relative] == sha(source)
                    units = HEADER_UNITS.get(source.name, [source.name])
                    results = report.get('checks', report.get('results', []))
                    for unit in units:
                        for standard in ['c++17', 'c++20']:
                            assert any(r.get('file', r.get('source')) == unit
                                       and r.get('standard') == standard
                                       and r.get('passed') is True for r in results), (sid, unit, standard)
                    item['source_test_mapping'].append({
                        'source_path': relative, 'source_sha256': sha(source),
                        'relation': relation, 'suite_id': suite,
                        'tested_translation_units': units,
                        'current_report_binding': 'exact_source_hash_and_passed_unit_checks',
                    })
                item['verification'] = ('bound_to_current_recheck' if item['source_test_mapping']
                                        else 'editorial_read_without_exact_compilation_binding')
                if kind == 'full_program':
                    assert item['source_test_mapping'], ('Unbound full program', sid, index)
                    prior_program_mappings = item['source_test_mapping']
                elif combined:
                    item['assembly_group'] = 'teaching_shared'
                    assert item['source_test_mapping']
                    prior_program_mappings = item['source_test_mapping']
                elif sid == 3570303 and index == 2 or sid in {3570304, 3570333}:
                    item['assembly_group'] = 'rbt_header'
                    assert item['source_test_mapping']
                if sid == 3569964 and index == 1:
                    item['execution_policy'] = 'Do not execute the deliberately leaking raw-pointer fragment.'
                if sid == 3570281 and index == 2:
                    item['requires_lesson_header'] = 'pre_index 1: avl.hpp'
                if sid == 4035481 and index == 2:
                    item['requires_lesson_header'] = 'pre_index 1: hash_table.hpp'
            entries.append(item)
    teaching_source = ROOT/SUITE_DIRS['t5b']/'teaching_shared.cpp'
    assert '\n\n'.join(cpp_by_id[3570213])+'\n' == teaching_source.read_text()
    rb_source = ROOT/SUITE_DIRS['t6']/'rbt.hpp'
    rb = '#pragma once\n'+'\n\n'.join([cpp_by_id[3570303][1]]
                                      + cpp_by_id[3570304] + cpp_by_id[3570333])+'\n'
    assert rb == rb_source.read_text()
    counts = Counter(item['kind'] for item in entries)
    unbound = [{'step_id': item['step_id'], 'pre_index': item['pre_index']}
              for item in entries if item['kind'] == 'fragment' and not item['source_test_mapping']]
    result = {
        'schema_version': 1, 'scope': 'All 91 text steps in modules 12–19, effective snapshot + LINKS + current advanced corrections.',
        'pre_index_base': 1,
        'hash_convention': 'decoded_sha256 hashes UTF-8 of the HTML-decoded pre content after removing markup, without whitespace normalization; raw_pre_sha256 includes the complete pre element.',
        'classification_note': 'output includes expected output and labelled sample input. A complete main with a preceding lesson header is a full_program translation unit with its dependency recorded; two TeachingShared parts form one program.',
        'counts': {'text_steps': 91, 'pre_blocks': len(entries), **dict(counts),
                   'assembled_full_programs_from_fragment_blocks': 1,
                   'full_program_units_with_current_test_binding': counts['full_program']+1,
                   'fragments_without_exact_compilation_binding': len(unbound)},
        'suites': suites,
        'assemblies': [
            {'id': 'teaching_shared', 'kind': 'full_program',
             'parts': [{'step_id': 3570213, 'pre_index': 1}, {'step_id': 3570213, 'pre_index': 2}],
             'source_path': teaching_source.relative_to(ROOT).as_posix(), 'source_sha256': sha(teaching_source),
             'recipe': 'strip each decoded pre, join with two LF, append LF; exact file equality asserted'},
            {'id': 'rbt_header', 'kind': 'header',
             'parts': [{'step_id': 3570303, 'pre_indices': [2]},
                       {'step_id': 3570304, 'pre_indices': list(range(1, 9))},
                       {'step_id': 3570333, 'pre_indices': list(range(1, 9))}],
             'source_path': rb_source.relative_to(ROOT).as_posix(), 'source_sha256': sha(rb_source),
             'recipe': '#pragma once + LF, stripped decoded parts joined by two LF, append LF; exact file equality asserted'},
        ],
        'fragments_without_exact_compilation_binding': unbound,
        'limitations': [
            'Semantic reading of all steps is recorded separately; source hashing does not establish teaching clarity.',
            'Only exact source bindings and actual passed current suite checks support current runtime coverage.',
            'Unbound fragments were read in context; no claim that every fragment was separately compiled.',
            'Expected failures in historical/current test harnesses are not automatically extra lesson pre blocks.',
            'No Stepik access, learner submissions or graded-step changes.'],
        'steps': step_index, 'blocks': entries,
    }
    target = PACKAGE/'code_inventory_advanced.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result['counts']))


if __name__ == '__main__':
    main()
