#!/usr/bin/env python3
"""Deterministic inventory of every pre block in the independently read core scope."""
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
ROOT = PACKAGE.parents[2]
OUTPUT = PACKAGE / 'code_inventory_core.json'


class PreBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.current = []
        self.language = None
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.active = True
            self.current = []
            self.language = None
        if tag == 'code' and self.active:
            classes = dict(attrs).get('class', '').split()
            self.language = next((s[9:] for s in classes if s.startswith('language-')), None)

    def handle_endtag(self, tag):
        if tag == 'pre' and self.active:
            self.blocks.append((''.join(self.current), self.language))
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.current.append(data)


def sha(data):
    return hashlib.sha256(data).hexdigest()


SUITES = {
    't2': ('theory-continuation-2026-11-23/examples/t2', 'validation/recheck/t2.json'),
    't3': ('theory-2026-11-23/examples/t3', 'validation/recheck/t3.json'),
    't4': ('theory-continuation-2026-11-23/examples/t4', 'validation/recheck/t4.json'),
    'links_types': ('theory-links-2026-11-23/examples/types', 'validation/recheck/links_types.json'),
    'new_core': ('theory-final-review-2026-11-23/examples/core', 'validation/new_core.json'),
}
COMPOSITE = {
    (3212951, 1): 'factorial/header',
    (3212951, 2): 'factorial/implementation',
    (3212951, 3): 'factorial/application_main',
    (3214991, 1): 'objects/header',
    (3214991, 2): 'objects/definitions',
    (3214991, 3): 'objects/application_main',
    (3253429, 1): 'interesting/header',
    (3253429, 2): 'interesting/implementation',
    (3253429, 3): 'interesting/application_main',
    (3253503, 1): 'interesting/test_main',
    (3253553, 1): 'gtest/test_component_with_library_main',
}
EXPECTED_FAILURES = {(3212989, 2), (3214873, 2)}


def classify(key, code, language):
    if key in COMPOSITE:
        return 'multi_file_component'
    if key in EXPECTED_FAILURES:
        return 'expected_failure'
    if language in ('cpp', 'c'):
        return 'full_program' if re.search(r'\bint\s+main\s*\(', code) else 'fragment'
    if language == 'cmake':
        return 'build_configuration'
    if language == 'bash' or re.match(r'\s*(?:cmake|g\+\+|ctest)\s', code):
        return 'command'
    return 'output'


def suite_for(path):
    for name, (directory, report) in SUITES.items():
        suite_root = ROOT / 'improvements/86957' / directory
        if path.is_relative_to(suite_root):
            return {
                'suite': name,
                'verifier': (suite_root / 'verify.py').relative_to(ROOT).as_posix(),
                'current_report': (PACKAGE / report).relative_to(ROOT).as_posix(),
            }
    return None


def confirm_report_source(path, suite_name):
    directory, relative = SUITES[suite_name]
    report = json.loads((PACKAGE / relative).read_text())
    assert report['status'] == 'passed', suite_name
    recorded = dict(report.get('input_sha256', {}))
    recorded.update({item['path']: item['sha256'] for item in report.get('sources', [])})
    source_package = ROOT / 'improvements/86957' / directory.split('/examples/')[0]
    keys = [path.relative_to(ROOT).as_posix(), path.relative_to(source_package).as_posix()]
    expected = sha(path.read_bytes())
    assert any(recorded.get(key) == expected for key in keys), (suite_name, path)


def build():
    index = json.loads((PACKAGE / 'review_inputs.json').read_text())
    rows = [r for r in index['steps'] if 5 <= r['module_number'] <= 11]
    assert len(rows) == 96
    changes = {r['step_id']: r for r in json.loads((PACKAGE / 'changes_core.json').read_text())}
    sources = {}
    for directory, _ in SUITES.values():
        for path in (ROOT / 'improvements/86957' / directory).rglob('*'):
            if path.is_file() and (path.suffix in {'.cpp', '.c', '.hpp', '.inc'} or path.name == 'CMakeLists.txt'):
                sources[path] = path.read_text()
    entries = []
    step_inputs = []
    for row in rows:
        before_path = ROOT / row['effective_path']
        assert sha(before_path.read_bytes()) == row['file_sha256'], row['step_id']
        path = PACKAGE / changes[row['step_id']]['path'] if row['step_id'] in changes else before_path
        document = json.loads(path.read_text())
        parser = PreBlocks()
        parser.feed(document['block']['text'])
        raw = re.findall(r'<pre\b[^>]*>.*?</pre>', document['block']['text'], re.S)
        assert len(raw) == len(parser.blocks)
        step_inputs.append({
            'step_id': row['step_id'], 'module_number': row['module_number'],
            'previous_effective_path': row['effective_path'],
            'previous_file_sha256': row['file_sha256'], 'previous_text_sha256': row['text_sha256'],
            'reviewed_final_path': path.relative_to(ROOT).as_posix(),
            'reviewed_final_file_sha256': sha(path.read_bytes()),
            'reviewed_final_text_sha256': sha(document['block']['text'].encode()),
            'pre_count': len(parser.blocks),
        })
        for pre_index, (code, language) in enumerate(parser.blocks, 1):
            key = (row['step_id'], pre_index)
            kind = classify(key, code, language)
            item = {
                'step_id': row['step_id'], 'module_number': row['module_number'],
                'pre_index': pre_index, 'kind': kind, 'language': language,
                'sha256': sha(code.encode()), 'raw_pre_sha256': sha(raw[pre_index - 1].encode()),
                'has_main': bool(re.search(r'\bint\s+main\s*\(', code)),
                'source_bindings': [], 'verification_bindings': [],
            }
            if key in COMPOSITE:
                item['component'] = COMPOSITE[key]
            for source, text in sorted(sources.items()):
                if text.strip() == code.strip():
                    item['source_bindings'].append({
                        'path': source.relative_to(ROOT).as_posix(), 'sha256': sha(source.read_bytes()),
                        'match': 'exact_decoded_bytes' if text == code else 'equal_after_trimming_outer_whitespace',
                    })
                    binding = suite_for(source)
                    if binding:
                        confirm_report_source(source, binding['suite'])
                        item['source_bindings'][-1]['source_sha256_matches_current_report'] = True
                    if binding and binding not in item['verification_bindings']:
                        item['verification_bindings'].append(binding)
            if row['step_id'] == 3177298:
                harness = HERE / 'array_variants.cpp'
                assert code in harness.read_text()
                confirm_report_source(harness, 'new_core')
                item['source_bindings'].append({
                    'path': harness.relative_to(ROOT).as_posix(), 'sha256': sha(harness.read_bytes()),
                    'match': 'exact_fragment_embedded_in_author_wrapper',
                    'source_sha256_matches_current_report': True,
                })
                item['verification_bindings'] = [suite_for(harness)]
                item['verification_detail'] = 'Compiled in a separate scope; the first array is fully assigned before any read.'
            elif key in EXPECTED_FAILURES:
                item['verification_bindings'] = [suite_for(HERE / 'verify.py')]
                item['verification_detail'] = 'The exact decoded fragment is inserted in an author wrapper and rejected in C++17 and C++20.'
            elif key == (3215112, 1):
                directory, _ = SUITES['t4']
                item['verification_bindings'] = [suite_for(ROOT / 'improvements/86957' / directory / 'verify.py')]
                item['verification_detail'] = 'T4 extracts this exact fragment into a function wrapper and checks answer.dat bytes.'
            elif key == (3214974, 2):
                item['verification_detail'] = 'Exact auto_aliases.inc is embedded in semantic_checks.cpp and type/value checks; two writes through const references are rejected.'
            if kind == 'command':
                item['coverage'] = 'Read for consistency; this command block is not claimed to have been executed literally.'
            elif kind == 'output':
                item['coverage'] = 'Expected output, not a compilable program. Relevant program output is covered only by its own binding.'
            elif item['verification_bindings']:
                item['coverage'] = 'Mapped to the named verifier and current report; the inventory itself does not execute code.'
            else:
                item['coverage'] = 'Read semantically; no separate compiler/run claim for this fragment.'
            entries.append(item)
    counts = Counter(entry['kind'] for entry in entries)
    assert len(entries) == 125
    assert all(e['verification_bindings'] for e in entries if e['kind'] in {'full_program', 'multi_file_component', 'expected_failure', 'build_configuration'})
    reports = {}
    for name, (_, relative) in SUITES.items():
        path = PACKAGE / relative
        value = json.loads(path.read_text())
        assert value['status'] == 'passed', name
        reports[name] = {'path': path.relative_to(ROOT).as_posix(),
                         'sha256': sha(path.read_bytes()), 'status': value['status']}
    return {
        'schema_version': 1,
        'scope': 'All 96 text steps in modules 5–11; effective snapshot plus prior theory-links overlay and the one new prose correction.',
        'input_index_sha256': sha((PACKAGE / 'review_inputs.json').read_bytes()),
        'sha256_definition': 'UTF-8 bytes of HTMLParser-decoded pre content; raw_pre_sha256 includes original pre markup.',
        'pre_index_base': 1,
        'counts': {'steps': len(rows), 'pre_blocks': len(entries), 'by_kind': dict(sorted(counts.items())),
                   'blocks_with_main': sum(e['has_main'] for e in entries),
                   'full_programs_with_verifier_binding': sum(e['kind'] == 'full_program' and bool(e['verification_bindings']) for e in entries)},
        'current_reports': reports,
        'step_inputs': step_inputs,
        'entries': entries,
        'limits': [
            'Semantic reading covers all 96 texts, including inline examples; the code inventory enumerates pre blocks only.',
            'A multi-file main is a component, not a standalone executable; components require their named companion sources.',
            'Matching an existing file is not by itself proof of execution: the specific verifier and new report are given separately.',
            'Historical suites were rerun by the integrator in isolation; this inventory does not rerun them or change historical reports.',
            'No claim that every fragment or command was compiled or executed; unbound fragments and literal command blocks are explicitly marked.',
            'This is not a review of module 20, assessed tasks, video steps, or live Stepik.',
        ],
    }


def main():
    result = json.dumps(build(), ensure_ascii=False, indent=2) + '\n'
    if '--check' in sys.argv:
        assert OUTPUT.read_text() == result, 'Core inventory is stale.'
        print('Core inventory matches all 96 texts and 125 pre blocks.')
    else:
        OUTPUT.write_text(result)
        print('Wrote ' + str(OUTPUT.relative_to(ROOT)))


if __name__ == '__main__':
    main()
