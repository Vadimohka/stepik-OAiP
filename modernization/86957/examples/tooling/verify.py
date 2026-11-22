#!/usr/bin/env python3
"""Validate the CMake practice and its shared implementation without networking."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--cmake', default='cmake')
    parser.add_argument('--compiler', default='g++')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    repo = here.parents[3]
    stage = here.parents[1]
    manifest = json.loads((here / 'examples.json').read_text())
    cmake = str(Path(shutil.which(args.cmake) or args.cmake).resolve())
    ctest = str(Path(cmake).with_name('ctest'))
    checks = []

    def run(command, *, expected=0, data=None):
        result = subprocess.run(command, input=data, text=True, capture_output=True, timeout=90)
        if result.returncode != expected:
            raise AssertionError({'command':command, 'expected':expected,
                                  'returncode':result.returncode,
                                  'stdout':result.stdout, 'stderr':result.stderr})
        return result

    changes = json.loads((stage / 'tooling_changes.json').read_text())['changes']
    for change in changes:
        before = json.loads((repo / change['source_path']).read_text())
        after = json.loads((repo / change['path']).read_text())
        old_text = before['block'].pop('text')
        new_text = after['block'].pop('text')
        if before != after or old_text == new_text:
            raise AssertionError(change['step_id'])
    checks.append({'check':'text_only_changes', 'steps':len(changes), 'passed':True})

    for item in manifest['embedded_files']:
        step = next((stage / 'steps' / str(item['lesson_id'])).glob(f"*_{item['step_id']}_text.step"))
        text = json.loads(step.read_text())['block']['text']
        snippets = [html.unescape(x) for x in re.findall(r'<pre><code[^>]*>(.*?)</code></pre>',text,re.S)]
        source = (here / item['path']).read_text()
        if source not in snippets:
            raise AssertionError({'file':item['path'], 'reason':'embedded code differs'})
    checks.append({'check':'embedded_files_match', 'files':len(manifest['embedded_files']), 'passed':True})

    with tempfile.TemporaryDirectory(prefix='tooling-verify-') as temporary:
        tmp = Path(temporary)
        for project in ['hello', 'interesting']:
            for config in ['Debug', 'Release']:
                build = tmp / (project + '-' + config)
                run([cmake,'-S',str(here/project),'-B',str(build),'-G','Unix Makefiles',
                     '-DCMAKE_BUILD_TYPE='+config, '-DCMAKE_CXX_COMPILER='+args.compiler,
                     '-DCMAKE_CXX_FLAGS=-Werror'])
                run([cmake,'--build',str(build)])
                if project == 'hello':
                    result = run([str(build/'hello')])
                    if result.stdout != 'Hello C++\n':
                        raise AssertionError(result.stdout)
                else:
                    result = run([ctest,'--test-dir',str(build),'--output-on-failure','--no-tests=error'])
                    if '100% tests passed' not in result.stdout:
                        raise AssertionError(result.stdout)
                    result = run([str(build/'interesting_tests')])
                    if result.stdout != '13 checks passed\n':
                        raise AssertionError(result.stdout)
                    for case in manifest['application_cases']:
                        result = run([str(build/'interesting_app')],expected=case['exit_code'],data=case['stdin'])
                        if result.stdout != case['stdout'] or result.stderr != case['stderr']:
                            raise AssertionError({'case':case,'stdout':result.stdout,'stderr':result.stderr})
                checks.append({'check':'cmake_build_and_run', 'project':project,'configuration':config,'passed':True})

        # Direct strict builds validate both the documented base and older-compatible code.
        for standard in ['c++17','c++20']:
            binary = tmp / ('tests-'+standard)
            run([args.compiler,'-std='+standard,'-Wall','-Wextra','-Wpedantic','-Werror',
                 '-DNDEBUG',str(here/'interesting/tests.cpp'),str(here/'interesting/interesting.cpp'),
                 '-o',str(binary)])
            result = run([str(binary)])
            if result.stdout != '13 checks passed\n':
                raise AssertionError(result.stdout)
            checks.append({'check':'strict_direct_build','standard':standard,'NDEBUG':True,'passed':True})

        # Fail a real CTest run after changing an expected value in an isolated copy.
        negative = tmp/'negative-source'
        shutil.copytree(here/'interesting',negative)
        test_source = negative/'tests.cpp'
        test_source.write_text(test_source.read_text().replace('Check(9, 1)','Check(9, 2)'))
        negative_build = tmp/'negative-build'
        run([cmake,'-S',str(negative),'-B',str(negative_build),'-G','Unix Makefiles',
             '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER='+args.compiler])
        run([cmake,'--build',str(negative_build)])
        result = run([str(negative_build/'interesting_tests')],expected=1)
        if result.stderr != 'n=9: expected 2, got 1\n':
            raise AssertionError(result.stderr)
        result = subprocess.run([ctest,'--test-dir',str(negative_build),'--output-on-failure','--no-tests=error'],
                                text=True,capture_output=True,timeout=30)
        if result.returncode == 0 or 'n=9: expected 2, got 1' not in result.stdout:
            raise AssertionError({'returncode':result.returncode,'stdout':result.stdout})
        checks.append({'check':'incorrect_expectation_fails_ctest','configuration':'Release','passed':True})

        # Restore expectations and mutate the production formula instead.
        test_source.write_text((here/'interesting/tests.cpp').read_text())
        implementation = negative/'interesting.cpp'
        implementation.write_text(implementation.read_text().replace('(interval_end + 1) / 10','interval_end / 10'))
        run([cmake,'--build',str(negative_build)])
        result = run([str(negative_build/'interesting_tests')],expected=1)
        if 'n=9: expected 1, got 0' not in result.stderr:
            raise AssertionError(result.stderr)
        checks.append({'check':'off_by_one_implementation_fails','configuration':'Release','passed':True})

        # An independent digit-sum reference checks the original mathematical contract.
        source = tmp/'oracle.cpp'
        source.write_text('''#include "interesting.hpp"
#include <iostream>
long long sum_digits(long long x) {
    long long sum = 0;
    do { sum += x % 10; x /= 10; } while (x != 0);
    return sum;
}
int main() {
    long long expected = 0;
    for (long long n = 0; n <= 10000; ++n) {
        if (n > 0 && sum_digits(n + 1) < sum_digits(n)) ++expected;
        if (CountInterestingInInterval(n) != expected) return 1;
    }
    std::cout << "10001 reference comparisons passed\\n";
}
''')
        binary=tmp/'oracle'
        run([args.compiler,'-std=c++20','-Wall','-Wextra','-Wpedantic','-Werror',
             '-I',str(here/'interesting'),str(source),str(here/'interesting/interesting.cpp'),'-o',str(binary)])
        result=run([str(binary)])
        if result.stdout != '10001 reference comparisons passed\n':
            raise AssertionError(result.stdout)
        checks.append({'check':'independent_digit_sum_oracle','inputs':10001,'passed':True})

    report = {'all_passed':True,
              'compiler':run([args.compiler,'--version']).stdout.splitlines()[0],
              'cmake':run([cmake,'--version']).stdout.splitlines()[0],
              'scope':'Linux/GCC; Windows/MSVC and GoogleTest integration not executed.',
              'checks':checks}
    (here/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    main()
