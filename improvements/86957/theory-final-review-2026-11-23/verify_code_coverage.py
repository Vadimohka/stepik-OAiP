#!/usr/bin/env python3
"""Reproduce/check the final theory code ledger without compiling or editing inputs.

Checks actual decoded pre bytes, exact/outer-whitespace source identities,
current report input hashes, test records or pinned aggregate verifiers, and
the two explicit source-assembly recipes. --check writes nothing.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from copy import deepcopy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
OLD = 'improvements/86957/theory-2026-11-23'
CONTINUATION = 'improvements/86957/theory-continuation-2026-11-23'
LINKS = 'improvements/86957/theory-links-2026-11-23'
SUITE_ROOTS = {
    't1': f'{OLD}/examples/t1', 't1b': f'{CONTINUATION}/examples/t1b',
    't2': f'{CONTINUATION}/examples/t2', 't3': f'{OLD}/examples/t3',
    't4': f'{CONTINUATION}/examples/t4', 't5': f'{CONTINUATION}/examples/t5',
    't5b': f'{CONTINUATION}/examples/t5b', 't6': f'{OLD}/examples/t6',
    'links_types': f'{LINKS}/examples/types',
    'new_core': str(PACKAGE.relative_to(ROOT) / 'examples/core'),
    'new_foundations': str(PACKAGE.relative_to(ROOT) / 'examples/foundations'),
}


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return sha_bytes(path.read_bytes())


def load(path):
    return json.loads(path.read_text())


def relative(path):
    return path.relative_to(ROOT).as_posix()


class PreBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            assert self.current is None, 'Nested pre is unsupported'
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'pre':
            assert self.current is not None
            self.blocks.append(''.join(self.current))
            self.current = None


def pre_blocks(document):
    parser = PreBlocks()
    parser.feed(document['block']['text'])
    assert parser.current is None
    return parser.blocks


def literal_assignment(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f'Missing literal assignment {name}')


class Evidence:
    def __init__(self):
        self.suites = {}

    def suite(self, name):
        if name == 'foundations':
            name = 'new_foundations'
        if name in self.suites:
            return self.suites[name]
        folder = ROOT / SUITE_ROOTS[name]
        verifier = folder / 'verify.py'
        report_path = PACKAGE / ('validation/' + name + '.json' if name.startswith('new_')
                                 else 'validation/recheck/' + name + '.json')
        report = load(report_path)
        assert report['status'] == 'passed', report_path
        source_package = folder.parents[1]
        hashes = {}
        if 'input_sha256' in report:
            recorded_hashes = report['input_sha256']
        else:
            assert name == 'links_types'
            recorded_hashes = {row['path']: row['sha256']
                               for row in report['sources'] + report['step_inputs']}
            for row in report['step_inputs']:
                assert sha_bytes(load(ROOT / row['path'])['block']['text'].encode()) == row['text_sha256']
        for raw_path, digest in recorded_hashes.items():
            path = ROOT / raw_path if raw_path.startswith(('improvements/', 'courses/')) else source_package / raw_path
            assert sha(path) == digest, ('Stale report input', name, path)
            key = relative(path)
            assert key not in hashes or hashes[key] == digest
            hashes[key] = digest
        assert hashes.get(relative(verifier)) == sha(verifier), ('Unbound verifier', name)
        public = {
            'suite_id': name, 'verifier_path': relative(verifier),
            'verifier_sha256': sha(verifier), 'report_path': relative(report_path),
            'report_sha256': sha(report_path), 'status': report['status'],
            'input_sha256_checked': len(hashes),
        }
        if not name.startswith('new_'):
            execution_path = report_path.with_name(name + '_execution.json')
            execution = load(execution_path)
            assert execution['status'] == execution['reported_status'] == 'passed'
            assert execution['exit_code'] == 0
            assert execution['verifier_path'] == relative(verifier)
            assert execution['verifier_sha256'] == sha(verifier)
            assert execution['report_sha256'] == sha(report_path)
            public['execution_record_path'] = relative(execution_path)
            public['execution_record_sha256'] = sha(execution_path)
            public['executed_at'] = execution['started_at']
        else:
            public['executed_at'] = report['started_at']
        record = {'name': name, 'folder': folder, 'report': report, 'hashes': hashes,
                  'verifier_text': verifier.read_text(), 'public': public}
        self.suites[name] = record
        return record

    def source(self, suite_name, source_path, expected_sha=None):
        suite = self.suite(suite_name)
        path = ROOT / source_path
        actual = sha(path)
        assert suite['hashes'].get(source_path) == actual, ('Source absent/stale in report', suite_name, source_path)
        if expected_sha is not None:
            assert actual == expected_sha, source_path
        return path

    def dependencies(self, suite_name, source_path):
        """Only local quoted includes, not a claim to hash the whole toolchain."""
        found = {}

        def visit(path):
            for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"', path.read_text(), re.M):
                dependency = (path.parent / name).resolve()
                if not dependency.is_file():
                    # Some T3 components use a CMake/explicit -I include directory.
                    matches = [ROOT / p for p in self.suite(suite_name)['hashes'] if Path(p).name == name]
                    assert matches, ('Unresolved local include', source_path, name)
                    dependency = matches[0]
                key = relative(dependency)
                if key in found:
                    continue
                self.source(suite_name, key)
                found[key] = sha(dependency)
                visit(dependency)
        visit(ROOT / source_path)
        return found

    def unit(self, suite_name, source_path, *, units=None):
        suite = self.suite(suite_name)
        report, name = suite['report'], suite['name']
        source = self.source(name, source_path)
        standards = ['c11', 'c17'] if source.suffix == '.c' else ['c++17', 'c++20']
        if units is None:
            if name == 'links_types' and source.name == 'auto_aliases.inc':
                units = ['semantic_checks.cpp']
                assert source.read_text() in (suite['folder'] / units[0]).read_text()
            elif name == 't3' and (source.suffix == '.hpp' or source.name == 'CMakeLists.txt'):
                project = source.parent.name
                units = {
                    'factorial': ['factorial/factorial.cpp', 'factorial/main.cpp'],
                    'objects': ['objects/objects.cpp', 'objects/main.cpp'],
                    'interesting': ['interesting/interesting.cpp', 'interesting/main.cpp', 'interesting/tests.cpp'],
                    'gtest': ['gtest/interesting.cpp', 'gtest/gtest_assertions.cpp'],
                }[project]
            else:
                units = [source.name]
        proof = {'suite_id': name, 'report_path': suite['public']['report_path'],
                 'report_sha256': suite['public']['report_sha256'],
                 'source_path': source_path, 'source_sha256': sha(source),
                 'standards': standards, 'tested_translation_units': units,
                 'test_evidence': []}
        for unit in units:
            if unit != source.name:
                self.source(name, relative(suite['folder'] / unit))
            for standard in standards:
                detail = {'translation_unit': unit, 'standard': standard}
                if name == 't2':
                    matches = [r for r in report['programs'] if r['file'] == unit and r['standard'] == standard]
                    assert len(matches) == 1 and matches[0]['status'] == 'passed' and matches[0]['cases'] > 0
                    detail.update(evidence='per_source_report', cases=matches[0]['cases'])
                elif name in {'t4', 't5', 't5b', 't6'}:
                    results = report.get('checks', report.get('results', []))
                    matches = [r for r in results if isinstance(r, dict)
                               and r.get('file', r.get('source')) == unit and r.get('standard') == standard]
                    assert matches and all(r.get('passed') is True for r in matches), (name, unit, standard)
                    detail.update(evidence='per_source_report', passed_records=len(matches))
                elif name == 'links_types':
                    compiled = [r for r in report['checks'] if r.get('kind') == 'compile'
                                and r.get('source') == unit and r.get('standard') == standard]
                    executed = [r for r in report['checks'] if r.get('kind') == 'run'
                                and r.get('program') == Path(unit).stem and r.get('standard') == standard]
                    assert compiled and executed and all(r['result'] == 'passed' for r in compiled + executed)
                    detail.update(evidence='compile_and_run_records', runtime_cases=len(executed))
                elif name == 'new_core':
                    compiled = [r for r in report['checks'] if r.get('kind') == 'compilation'
                                and r.get('source') == unit and r.get('standard') == standard]
                    executed = [r for r in report['checks'] if r.get('kind') == 'execution'
                                and r.get('source') == unit and r.get('standard') == standard]
                    assert len(compiled) == len(executed) == 1 and all(r['passed'] for r in compiled + executed)
                    detail.update(evidence='compile_and_run_records', runtime_cases=1)
                elif name == 'new_foundations':
                    bindings = literal_assignment(suite['verifier_text'], 'BINDINGS')
                    assert unit in bindings
                    executed = [r for r in report['runtime_cases'] if r['program'] == unit and r['standard'] == standard]
                    assert executed and all(r['status'] == 'passed' for r in executed)
                    assert report['counts']['successful_compilations'] == 2 * (len(bindings) + 1)
                    detail.update(evidence='exact_binding_and_runtime_records', runtime_cases=len(executed))
                elif name == 't1b':
                    bindings = literal_assignment(suite['verifier_text'], 'BINDINGS')
                    assert unit in bindings
                    prefix = standard + '/' + ('checked-input/' if unit == 'checked_input.cpp' else unit + '/')
                    matched = [r for r in report['runtime_cases'] if r.startswith(prefix)]
                    assert matched, (name, unit, standard)
                    detail.update(evidence='exact_binding_and_named_runtime_records', runtime_cases=len(matched))
                elif name == 't3':
                    assert standard in report['standards']
                    assert 'Exact HTML/source equality and text-only payloads: passed' in report['checks']
                    within = source.relative_to(suite['folder']).as_posix()
                    if within.startswith('functions/'):
                        cases_path = suite['folder'] / 'function_cases.json'
                        self.source(name, relative(cases_path))
                        cases = load(cases_path)['examples']
                        matches = [r for r in cases if r['source'] == unit]
                        assert len(matches) == 1 and matches[0]['cases']
                        assert "compile([HERE/'functions'/spec['source']],binary,std)" in suite['verifier_text']
                        detail.update(evidence='aggregate_run_with_exact_fixture_and_pinned_loop',
                                      fixture_path=relative(cases_path), cases=len(matches[0]['cases']))
                    elif within.startswith('factorial/'):
                        assert all(f'factorial {standard} shared={shared}: boundaries 0..20 and rejected input' in report['checks']
                                   for shared in ['OFF', 'ON'])
                        detail.update(evidence='named_static_and_shared_cmake_runs')
                    elif within.startswith('gtest/'):
                        assert f'GoogleTest pinned version, C++{standard[3:]}: both test cases passed' in report['checks']
                        detail.update(evidence='named_googletest_cmake_run')
                    elif within.startswith('interesting/'):
                        assert 'Exact interesting CMake/CTest Release example: passed' in report['checks']
                        assert within in suite['verifier_text']
                        detail.update(evidence='aggregate_run_with_pinned_direct_link_and_ctest')
                    elif within.startswith('objects/') or within == 'out_of_range.cpp':
                        assert within in suite['verifier_text']
                        detail.update(evidence='aggregate_run_with_pinned_named_direct_compile_and_run')
                    elif within == 'enumeration.cpp':
                        assert f'Independent enumeration vs formula: 0..1000 ({standard})' in report['checks']
                        detail.update(evidence='named_independent_enumeration_check')
                    else:
                        raise AssertionError(('Unmapped T3 unit', within))
                    assert report['counts']['direct_compilations'] == 38 and report['counts']['cmake_configurations'] == 7
                else:
                    raise AssertionError(('No proof rule for suite', name))
                proof['test_evidence'].append(detail)
        proof['local_dependency_sha256'] = self.dependencies(name, source_path)
        return proof

    def dynamic_t1(self, step_id, index, code, mode):
        suite = self.suite('t1')
        paths = list((ROOT / OLD / 'steps').glob(f'*/*_{step_id}_text.step'))
        assert len(paths) == 1
        source = paths[0]
        self.source('t1', relative(source))
        assert pre_blocks(load(source))[index] == code
        tree = ast.parse(suite['verifier_text'])
        selected = None
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple):
                names = [x.id for x in node.target.elts if isinstance(x, ast.Name)]
                if names == ['sid', 'expected']:
                    selected = ast.literal_eval(node.iter)
        assert selected == [(3201305, '250\n'), (3201179, 'Hello, C++!\n'), (3231317, 'Hello C++\n')]
        counts = suite['report']['counts']
        assert counts == {'compilations': 6, 'runtime_cases': 7,
                          'expected_compile_failures': 2, 'cmake_configurations': 1}
        if mode == 'expected_compile_failure':
            assert step_id == 3201189 and 'blocks(3201189)' in suite['verifier_text']
        else:
            assert step_id in dict(selected)
        return {
            'suite_id': 't1', 'report_path': suite['public']['report_path'],
            'report_sha256': suite['public']['report_sha256'],
            'source_step_path': relative(source), 'source_step_sha256': sha(source),
            'dynamic_extraction': {'step_id': step_id, 'pre_index': index, 'pre_index_base': 0},
            'standards': ['c++17', 'c++20'], 'verification_mode': mode,
            'test_evidence': 'Aggregate run; exact literal selection, pinned verifier hash, dynamic pre identity and execution sidecar checked.',
        }


def match_source(code, path, relation):
    source = path.read_text()
    if relation in {'exact_decoded_bytes', 'exact'}:
        assert source == code, path
    elif relation in {'equal_after_trimming_outer_whitespace', 'whole_file_ignoring_outer_whitespace'}:
        assert source.strip() == code.strip(), path
    elif relation in {'exact_fragment_embedded_in_author_wrapper', 'ordered_part_of_combined_program',
                      'ordered_part_of_assembled_header'}:
        assert code.strip() in source, path
    else:
        raise AssertionError(('Unknown source relation', relation))


def build():
    index_path = PACKAGE / 'review_inputs.json'
    manifest_path = PACKAGE / 'manifest.json'
    inputs, manifest = load(index_path), load(manifest_path)
    rows = inputs['steps']
    indexed = {r['step_id']: r for r in rows}
    overrides = {r['step_id']: r for r in manifest['steps']}
    assert len(indexed) == len(rows) == 283
    assert len(overrides) == len(manifest['steps']) == 55
    assert set(overrides) <= set(indexed)
    assert Counter(r['part'] for r in overrides.values()) == {'carried': 49, 'foundations': 3, 'core': 1, 'advanced': 2}
    final, final_inputs, bodies = {}, [], {}
    for sid, row in indexed.items():
        source = ROOT / row['effective_path']
        before = load(source)
        assert sha(source) == row['file_sha256']
        assert sha_bytes(before['block']['text'].encode()) == row['text_sha256']
        assert before['block']['name'] == 'text'
        target = ROOT / overrides[sid]['target_path'] if sid in overrides else source
        after = load(target)
        assert after['id'] == before['id'] and after['block']['name'] == 'text'
        restored = deepcopy(after)
        restored['block']['text'] = before['block']['text']
        assert restored == before, ('Non-text field changed', sid)
        old_pres, new_pres = pre_blocks(before), pre_blocks(after)
        assert old_pres == new_pres, ('A current prose-only revision changed code', sid)
        raw_pattern = r'<pre\b[^>]*>.*?</pre>'
        assert re.findall(raw_pattern, before['block']['text'], re.S) == re.findall(raw_pattern, after['block']['text'], re.S), ('Raw pre markup changed', sid)
        if sid in overrides:
            entry = overrides[sid]
            assert sha(target) == entry['after_file_sha256']
            assert entry['previous_effective_path'] == row['effective_path']
            assert entry['previous_effective_file_sha256'] == row['file_sha256']
            if entry['part'] == 'carried':
                assert target.read_bytes() == source.read_bytes(), ('Carried LINKS drift', sid)
            else:
                assert before['block']['text'] != after['block']['text']
        final[sid], bodies[sid] = target, new_pres
        final_inputs.append({'step_id': sid, 'module_number': row['module_number'],
                             'path': relative(target), 'file_sha256': sha(target),
                             'text_sha256': sha_bytes(after['block']['text'].encode()),
                             'pre_blocks': len(new_pres),
                             'role': overrides[sid]['part'] if sid in overrides else 'preserved'})

    evidence = Evidence()
    normalized, inventories = {}, {}
    for group, base, modules in [('foundations', 0, range(1, 5)), ('core', 1, range(5, 12)), ('advanced', 1, range(12, 20))]:
        path = PACKAGE / f'code_inventory_{group}.json'
        inventory = load(path)
        inventories[group] = inventory
        assert inventory.get('pre_index_base', 0) == base
        if group == 'advanced':
            for suite_name, declared in inventory['suites'].items():
                current = evidence.suite(suite_name)['public']
                assert declared['verifier_path'] == current['verifier_path']
                assert declared['verifier_sha256'] == current['verifier_sha256']
                assert declared['current_report_path'] == current['report_path']
                assert declared['current_report_sha256'] == current['report_sha256']
        if group == 'core':
            for suite_name, declared in inventory['current_reports'].items():
                current = evidence.suite(suite_name)['public']
                assert declared['path'] == current['report_path']
                assert declared['sha256'] == current['report_sha256']
        expected_steps = {r['step_id'] for r in rows if r['module_number'] in modules}
        if group == 'core':
            recorded_steps = {r['step_id'] for r in inventory['step_inputs']}
        elif group == 'advanced':
            recorded_steps = {r['step_id'] for r in inventory['steps']}
        else:
            # Foundations records all 96 source hashes in the full review even
            # when a text has no pre block.
            review = load(PACKAGE / 'review_foundations.json')
            recorded_steps = {r['step_id'] for r in review['review_inputs']}
            for r in review['review_inputs']:
                assert r['file_sha256'] == indexed[r['step_id']]['file_sha256']
        assert recorded_steps == expected_steps, ('Step inventory gap', group)
        entries = inventory.get('entries', inventory.get('blocks'))
        expected_keys = {(sid, i) for sid in expected_steps for i in range(len(bodies[sid]))}
        found_keys = set()
        for entry in entries:
            sid, index = entry['step_id'], entry['pre_index'] - base
            key = (sid, index)
            assert key in expected_keys and key not in found_keys and key not in normalized
            found_keys.add(key)
            code = bodies[sid][index]
            digest = entry.get('code_sha256', entry.get('decoded_sha256', entry.get('sha256')))
            assert digest == sha_bytes(code.encode()), ('Stale decoded pre', group, key)
            kind = 'shell_commands' if entry['kind'] == 'command' else entry['kind']
            has_main = bool(re.search(r'\b(?:int|auto)\s+main\s*\(', code))
            if kind == 'full_program':
                assert has_main
            if has_main:
                assert kind in {'full_program', 'multi_file_component', 'expected_failure'} or entry.get('assembly_group') == 'teaching_shared'
            item = {'step_id': sid, 'module_number': indexed[sid]['module_number'],
                    'pre_index': index, 'pre_index_base': 0, 'kind': kind,
                    'decoded_sha256': digest, 'final_step_path': relative(final[sid]),
                    'source_inventory': relative(path), 'source_pre_index': entry['pre_index'],
                    'source_pre_index_base': base, 'bindings': []}
            if group == 'foundations':
                for binding in entry['test_mapping']:
                    suite = binding['suite']
                    current_suite = evidence.suite(suite)['public']
                    assert binding['verifier_path'] == current_suite['verifier_path']
                    assert binding['current_report_path'] == current_suite['report_path']
                    mode = binding.get('verification_mode', 'compile_and_run')
                    if suite == 't1':
                        item['bindings'].append(evidence.dynamic_t1(sid, index, code, mode))
                    elif 'source_path' in binding:
                        source = evidence.source(suite, binding['source_path'], binding['source_sha256'])
                        match_source(code, source, 'exact')
                        if kind == 'expected_failure':
                            current = evidence.suite(suite)
                            assert sid == 3177250 and current['report']['counts']['expected_link_failures'] == 2
                            proof = {'suite_id': suite, 'source_path': relative(source), 'source_sha256': sha(source),
                                     'report_path': current['public']['report_path'],
                                     'report_sha256': current['public']['report_sha256'],
                                     'standards': ['c++17', 'c++20'],
                                     'verification_mode': 'compile_object_then_expected_link_failure',
                                     'test_evidence': 'Pinned T1B verifier with matching source hash and two expected link failures.'}
                        else:
                            proof = evidence.unit(suite, relative(source))
                        proof['source_relation'] = 'exact_decoded_bytes'
                        item['bindings'].append(proof)
                    else:
                        # Named T1B wrapped fragments; no standalone source file.
                        current = evidence.suite(suite)
                        old_step = ROOT / CONTINUATION / indexed[sid]['target_relative_path']
                        evidence.source(suite, relative(old_step))
                        assert pre_blocks(load(old_step))[index] == code
                        assert sid in {3177248, 3215092, 3201267}
                        if sid == 3201267:
                            assert current['report']['counts']['expected_compile_failures'] == 4
                        else:
                            label = 'include-fragment' if sid == 3177248 else 'scanf-defined-domain/'
                            for standard in ['c++17', 'c++20']:
                                assert any(r.startswith(standard + '/' + label) for r in current['report']['runtime_cases'])
                        item['bindings'].append({'suite_id': suite, 'report_path': current['public']['report_path'],
                                                 'report_sha256': current['public']['report_sha256'],
                                                 'source_step_path': relative(old_step), 'source_step_sha256': sha(old_step),
                                                 'verification_mode': mode, 'standards': ['c++17', 'c++20'],
                                                 'test_evidence': 'Pinned dynamic fragment extraction, wrapper and named runtime/expected-failure checks.'})
            elif group == 'core':
                for binding in entry['source_bindings']:
                    source = ROOT / binding['path']
                    assert sha(source) == binding['sha256']
                    match_source(code, source, binding['match'])
                    candidates = [v for v in entry['verification_bindings']
                                  if binding['path'] in evidence.suite(v['suite'])['hashes']]
                    assert candidates
                    for v in candidates:
                        declared_suite = evidence.suite(v['suite'])['public']
                        assert v['verifier'] == declared_suite['verifier_path']
                        assert v['current_report'] == declared_suite['report_path']
                        proof = evidence.unit(v['suite'], binding['path'])
                        proof['source_relation'] = binding['match']
                        item['bindings'].append(proof)
                if kind == 'expected_failure':
                    assert not entry['source_bindings']
                    current = evidence.suite('new_core')
                    matches = [c for c in current['report']['checks'] if c.get('kind') == 'expected_compilation_rejection'
                               and code.strip() in c['source']]
                    assert {r['standard'] for r in matches} == {'c++17', 'c++20'}
                    assert all(r['passed'] and r['returncode'] != 0 and sha_bytes(r['source'].encode()) == r['source_sha256'] for r in matches)
                    item['bindings'].append({'suite_id': 'new_core', 'report_path': current['public']['report_path'],
                                             'report_sha256': current['public']['report_sha256'],
                                             'verification_mode': 'expected_compile_failure_with_exact_embedded_fragment',
                                             'standards': ['c++17', 'c++20'],
                                             'fixture_sha256': sorted({r['source_sha256'] for r in matches})})
            else:
                if kind == 'output':
                    # Such records refer to the preceding program, not an
                    # identity between output text and a C++ source file.
                    item['data_role'] = entry.get('data_role', 'expected_output')
                    item['related_program_sources'] = [m['source_path'] for m in entry['source_test_mapping']]
                    for binding in entry['source_test_mapping']:
                        evidence.source(binding['suite_id'], binding['source_path'], binding['source_sha256'])
                else:
                    for binding in entry['source_test_mapping']:
                        source = evidence.source(binding['suite_id'], binding['source_path'], binding['source_sha256'])
                        match_source(code, source, binding['relation'])
                        proof = evidence.unit(binding['suite_id'], binding['source_path'], units=binding['tested_translation_units'])
                        proof['source_relation'] = binding['relation']
                        item['bindings'].append(proof)
                    if 'assembly_group' in entry:
                        item['assembly_group'] = entry['assembly_group']
                    if 'requires_lesson_header' in entry:
                        item['requires_lesson_header'] = entry['requires_lesson_header']
            if kind in {'full_program', 'multi_file_component', 'expected_failure'}:
                assert item['bindings'], ('Unbound required code', key, kind)
            item['coverage'] = ('bound_to_checked_current_evidence' if item['bindings'] else
                                'no_individual_compilation_or_execution_claim')
            normalized[key] = item
        assert found_keys == expected_keys, ('Missing/extra pre entries', group)

    # Exact reconstruction, rather than accepting substring matches alone.
    assemblies = []
    for assembly in inventories['advanced']['assemblies']:
        keys = []
        for part in assembly['parts']:
            indices = part.get('pre_indices', [part.get('pre_index')])
            keys.extend((part['step_id'], index - 1) for index in indices)
        joined = '\n\n'.join(bodies[sid][index].strip() for sid, index in keys) + '\n'
        if assembly['id'] == 'rbt_header':
            joined = '#pragma once\n' + joined
        else:
            assert assembly['id'] == 'teaching_shared'
        source = ROOT / assembly['source_path']
        assert joined == source.read_text() and sha(source) == assembly['source_sha256']
        suite = 't5b' if assembly['id'] == 'teaching_shared' else 't6'
        units = ['teaching_shared.cpp'] if suite == 't5b' else ['rbt_demo.cpp', 'invariants.cpp']
        proof = evidence.unit(suite, relative(source), units=units)
        assemblies.append({'id': assembly['id'], 'kind': assembly['kind'],
                           'parts': [{'step_id': sid, 'pre_index': index, 'pre_index_base': 0} for sid, index in keys],
                           'recipe': assembly['recipe'], 'exact_reconstruction': True, 'binding': proof})

    items = [normalized[key] for key in sorted(normalized)]
    kind_counts = Counter(item['kind'] for item in items)
    assert len(items) == 340 and kind_counts['full_program'] == 148
    assert kind_counts['multi_file_component'] == 11 and kind_counts['expected_failure'] == 5
    assert sum(a['kind'] == 'full_program' for a in assemblies) == 1
    full = [item for item in items if item['kind'] == 'full_program']
    c_programs = [item for item in full if any(b.get('standards') == ['c11', 'c17'] for b in item['bindings'])]
    assert len(c_programs) == 2
    gaps = [(3177281, 1), (3177281, 2), (3177283, 1), (3212990, 0),
            (3212989, 0), (3212989, 2), (3212989, 4)]
    for key in gaps:
        assert normalized[key]['kind'] == 'full_program'
        assert any(b['suite_id'] in {'new_core', 'new_foundations'} for b in normalized[key]['bindings'])
    unbound = [dict(step_id=i['step_id'], pre_index=i['pre_index'], kind=i['kind'])
               for i in items if not i['bindings']]
    result = {
        'schema_version': 1, 'status': 'passed', 'base_commit': inputs['base_commit'],
        'scope': 'Actual final effective text of all 283 steps in modules 1–19: 55 manifest overrides plus review_inputs; no Stepik access.',
        'pre_index_base': 0,
        'input_inventory_index_bases': {'foundations': 0, 'core': 1, 'advanced': 1},
        'counts': {
            'text_steps': len(indexed), 'pre_blocks': len(items), 'by_kind': dict(sorted(kind_counts.items())),
            'manifest_overrides': 55, 'carried_links_byte_identical': 49, 'new_prose_only_corrections': 6,
            'positive_full_listing_occurrences': 148, 'assembled_positive_programs': 1,
            'positive_program_units_including_assembly': 149,
            'cpp17_cpp20_full_listing_occurrences': 146, 'cpp17_cpp20_assembled_programs': 1,
            'c11_c17_full_listing_occurrences': 2,
            'multi_file_pre_components': 11, 'assembled_headers_from_fragments': 1,
            'expected_failure_pre_blocks': 5, 'newly_closed_full_listing_coverage_gaps': 7,
            'full_sources_with_expected_failure': sum(i['kind'] == 'expected_failure' and bool(re.search(r'\bint\s+main\s*\(', bodies[i['step_id']][i['pre_index']])) for i in items),
            'blocks_without_individual_execution_binding': len(unbound),
            'unbound_by_kind': dict(sorted(Counter(i['kind'] for i in unbound).items())),
            'current_suites_used': len(evidence.suites),
            'report_input_hashes_checked_including_repeated_inputs': sum(len(s['hashes']) for s in evidence.suites.values()),
            'unique_report_input_files_checked': len({p for s in evidence.suites.values() for p in s['hashes']}),
        },
        'evidence_rules': [
            'Every final pre is decoded independently with HTMLParser and matched to exactly one normalized inventory entry.',
            'All report input files and each pinned verifier are rehashed; isolated execution sidecars bind historical-suite report and verifier hashes.',
            'Static full-source matches are exact bytes or explicitly limited to outer whitespace. Source dependencies and named translation-unit checks are also verified.',
            'T1 and portions of T3 retain aggregate historical report formats. Their proof combines exact source/fixture/dynamic selection, a pinned successful verifier, and the current execution sidecar; no absent individual program log is invented.',
            'TeachingShared and RBT header are reconstructed byte-for-byte from ordered final fragments.',
            'A source binding for an output block is treated only as association with its program, not as source-code identity or a separate execution.',
        ],
        'input_sha256': {
            relative(index_path): sha(index_path), relative(manifest_path): sha(manifest_path),
            **{relative(PACKAGE / f'code_inventory_{name}.json'): sha(PACKAGE / f'code_inventory_{name}.json')
               for name in inventories},
            relative(Path(__file__).resolve()): sha(Path(__file__).resolve()),
        },
        'suites': {name: item['public'] for name, item in sorted(evidence.suites.items())},
        'final_step_inputs': sorted(final_inputs, key=lambda row: row['step_id']),
        'blocks': items, 'assemblies': assemblies,
        'newly_closed_coverage_gaps': [{'step_id': sid, 'pre_index': index, 'pre_index_base': 0}
                                       for sid, index in gaps],
        'without_individual_execution_binding': unbound,
        'limits': [
            'This checker performs no compilation, execution of C++ programs, network request, or Stepik operation; it verifies the current recorded execution evidence.',
            '148 is a count of positive full listing occurrences in texts, including repeated identical programs, not 148 unique binary executables. TeachingShared adds one assembled program unit.',
            'Two historical full listings are C11/C17; the remaining full listings and TeachingShared have C++17/C++20 evidence.',
            'Eleven T3 multi-file components and an assembled RBT header are accounted separately, not silently counted as independent standalone programs.',
            'Unbound fragments, shell commands, pseudocode, data and configuration are not claimed independently executed. Some commands/configurations were used by larger tested projects without individual pre-level logs.',
            'Source/hash correspondence and current author tests do not constitute a proof for all possible inputs or all C++ implementations. Recorded runs are Linux/GCC; Windows/MSVC and macOS are not claimed.',
        ],
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify evidence and require the saved ledger to match; write nothing.')
    args = parser.parse_args()
    result = build()
    target = PACKAGE / 'code_coverage.json'
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if args.check:
        assert target.read_bytes() == encoded, 'code_coverage.json is stale; regenerate after reviewing changed inputs'
    else:
        target.write_bytes(encoded)
    print(json.dumps({'status': 'checked' if args.check else 'written', 'counts': result['counts']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
