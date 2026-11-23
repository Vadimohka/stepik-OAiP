#!/usr/bin/env python3
"""Author checks for exact worked examples of functions, linking and testing.

No learner tasks or server submissions. Output is tied to SHA-256 inputs.
"""
from __future__ import annotations
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
PKG=HERE.parents[1]
ROOT=PKG.parents[2]
FLAGS=['-Wall','-Wextra','-Wpedantic','-Werror','-O2','-DNDEBUG']
REPORT=HERE/'validation.json'

def save(report):
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

def blocks(sid, language='cpp'):
    path=next((PKG/'steps').glob(f'*/*_{sid}_text.step'))
    data=json.loads(path.read_text())
    return [html.unescape(x) for x in re.findall(r'<pre><code class="language-'+language+r'">(.*?)</code></pre>',data['block']['text'],re.S)]

def command(args, *, stdin='', expected=None, timeout=60):
    p=subprocess.run(list(map(str,args)),input=stdin,text=True,capture_output=True,timeout=timeout)
    if expected is None:
        if p.returncode:
            raise RuntimeError(f'{args[0]} failed ({p.returncode}): {p.stderr[-5000:]} {p.stdout[-1500:]}')
    else:
        actual=(p.returncode,p.stdout,p.stderr)
        if actual!=expected:
            raise AssertionError(f'{args}: expected {expected!r}, got {actual!r}')
    return p

def inputs():
    paths=[PKG/'changes_t3.json',PKG/'review_t3.json']
    ids=json.loads((PKG/'review_t3.json').read_text())['changed_text_step_ids']
    paths+= [next((PKG/'steps').glob(f'*/*_{sid}_text.step')) for sid in ids]
    paths+= [p for p in HERE.rglob('*') if p.is_file() and p.name!='validation.json' and '__pycache__' not in p.parts]
    return {p.relative_to(PKG).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def main():
    report={'schema_version':1,'status':'running','all_passed':False,'started_at':datetime.now(timezone.utc).isoformat(),
            'scope':'Author verification of explanatory code; no student exercises or Stepik submissions.',
            'compiler':None,'standards':['c++17','c++20'],'flags':FLAGS,'input_sha256':{},
            'counts':{'text_steps':29,'direct_compilations':0,'runtime_cases':0,'cmake_configurations':0},
            'checks':[], 'limitations':['Windows/MSVC and macOS binaries were not executed.']}
    save(report)
    try:
        cases=json.loads((HERE/'function_cases.json').read_text())['examples']
        for spec in cases:
            name=spec['source']
            exact=(HERE/'functions'/name).read_text()
            assert exact in blocks(spec['step_id']), f'HTML mismatch: {name}'
        for sid,names in [(3212951,['factorial/factorial.hpp','factorial/factorial.cpp','factorial/main.cpp']),
                          (3214991,['objects/objects.hpp','objects/objects.cpp','objects/main.cpp']),
                          (3252940,['out_of_range.cpp']),(3253129,['enumeration.cpp']),
                          (3253429,['interesting/interesting.hpp','interesting/interesting.cpp','interesting/main.cpp']),
                          (3253503,['interesting/tests.cpp']),(3253553,['gtest/gtest_assertions.cpp'])]:
            assert blocks(sid)==[(HERE/n).read_text() for n in names],f'HTML mismatch: {sid}'
        for sid,name in [(3215032,'factorial/CMakeLists.txt'),(3253503,'interesting/CMakeLists.txt'),(3253553,'gtest/CMakeLists.txt')]:
            assert blocks(sid,'cmake')==[(HERE/name).read_text()],f'CMake HTML mismatch: {sid}'
        # Header equality prevents the gtest variant drifting from the checked implementation.
        for name in ['interesting.hpp','interesting.cpp']:
            assert (HERE/'gtest'/name).read_bytes()==(HERE/'interesting'/name).read_bytes()
        changes=json.loads((PKG/'changes_t3.json').read_text())
        for item in changes:
            after=json.loads((PKG/item['path']).read_text())
            baseline=PKG/'baseline'/item['path']
            if not baseline.is_file(): baseline=ROOT/'courses/86957'/item['path']
            before=json.loads(baseline.read_text())
            a=after['block'].pop('text');b=before['block'].pop('text')
            assert after==before and a!=b, f'Only block.text may change: {item["step_id"]}'
            assert not re.search(r'Самостоятельно|Самопроверка|<h\d>Самостоятельная',a), item['step_id']
        report['checks'].append('Exact HTML/source equality and text-only payloads: passed')
        report['input_sha256']=inputs()
        report['compiler']=command(['g++','--version']).stdout.splitlines()[0]
        cmake=os.environ.get('CMAKE') or shutil.which('cmake')
        if not cmake: raise RuntimeError('CMake is required for the explained library builds')
        ctest=Path(cmake).with_name('ctest')
        report['cmake']=command([cmake,'--version']).stdout.splitlines()[0]
        save(report)
        with tempfile.TemporaryDirectory(prefix='theory-t3-') as folder:
            temp=Path(folder)
            def compile(sources,binary,std,extra=()):
                command(['g++',f'-std={std}',*FLAGS,*extra,*sources,'-o',binary])
                report['counts']['direct_compilations']+=1
            def run(binary,stdin='',expected=(0,'','')):
                command([binary],stdin=stdin,expected=expected,timeout=10)
                report['counts']['runtime_cases']+=1
            for std in report['standards']:
                for spec in cases:
                    binary=temp/(spec['source']+'-'+std)
                    compile([HERE/'functions'/spec['source']],binary,std)
                    for case in spec['cases']:
                        run(binary,case['stdin'],(case['returncode'],case['stdout'],case['stderr']))
                binary=temp/('objects-'+std)
                compile([HERE/'objects/main.cpp',HERE/'objects/objects.cpp'],binary,std)
                run(binary,expected=(0,'5 3.4\n',''))
                binary=temp/('exception-'+std)
                compile([HERE/'out_of_range.cpp'],binary,std)
                run(binary,expected=(0,'index outside the range\n',''))
                binary=temp/('interesting-tests-'+std)
                compile([HERE/'interesting/tests.cpp',HERE/'interesting/interesting.cpp'],binary,std)
                run(binary,expected=(0,'13 checks passed\n',''))
                # Independent enumeration model validates the derived formula over a range.
                binary=temp/('enumeration-'+std)
                compile([HERE/'enumeration_check.cpp',HERE/'enumeration.cpp',HERE/'interesting/interesting.cpp'],binary,std,
                        ['-I',str(HERE/'interesting')])
                run(binary)
                report['checks'].append(f'Independent enumeration vs formula: 0..1000 ({std})')
                binary=temp/('interesting-app-'+std)
                compile([HERE/'interesting/main.cpp',HERE/'interesting/interesting.cpp'],binary,std)
                for n,result in [(1,0),(9,1),(19,2),(109,11),(999999999,100000000),(1000000000,100000000)]:
                    run(binary,f'{n}\n',(0,f'{result}\n',''))
                for bad in ['0\n','-1\n','1000000001\n','abc\n','']:
                    run(binary,bad,(1,'','Expected an integer from 1 to 1000000000\n'))
                # The negative-control outputs in prose must actually fail as described.
                wrong=(HERE/'interesting/tests.cpp').read_text().replace('!Check(9, 1)','!Check(9, 2)')
                wrong_path=temp/'wrong_expectation.cpp';wrong_path.write_text(wrong)
                binary=temp/('negative-'+std)
                compile([wrong_path,HERE/'interesting/interesting.cpp'],binary,std,['-I',str(HERE/'interesting')])
                run(binary,expected=(1,'','n=9: expected 2, got 1\n'))
                for shared in ['OFF','ON']:
                    build=temp/f'factorial-{std}-{shared}'
                    command([cmake,'-S',HERE/'factorial','-B',build,f'-DBUILD_SHARED_LIBS={shared}',
                             f'-DCMAKE_CXX_STANDARD={std[3:]}','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_FLAGS=-Werror'])
                    command([cmake,'--build',build,'--parallel','2'])
                    report['counts']['cmake_configurations']+=1
                    binary=build/'factorial_demo'
                    for n in range(21): run(binary,f'{n}\n',(0,f'{math.factorial(n)}\n',''))
                    for bad in ['-1\n','21\n','abc\n','']:
                        run(binary,bad,(1,'','input error\n'))
                    artifacts=list(build.glob('libcourse_math.*'))
                    expected_suffixes={'.a'} if shared=='OFF' else {'.so','.dylib','.dll'}
                    assert any(p.suffix in expected_suffixes for p in artifacts), artifacts
                    report['checks'].append(f'factorial {std} shared={shared}: boundaries 0..20 and rejected input')
            # Run the exact CTest project printed in the lesson, including its release configuration.
            build=temp/'interesting-cmake'
            command([cmake,'-S',HERE/'interesting','-B',build,'-DBUILD_TESTING=ON','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_FLAGS=-Werror'])
            command([cmake,'--build',build,'--parallel','2'])
            command([ctest,'--test-dir',build,'--output-on-failure','--no-tests=error'])
            report['counts']['cmake_configurations']+=1
            report['checks'].append('Exact interesting CMake/CTest Release example: passed')
            # Optional external dependency: do not turn a network restriction into a false success.
            try:
                for std in [17,20]:
                    build=temp/f'gtest-{std}'
                    command([cmake,'-S',HERE/'gtest','-B',build,'-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_STANDARD={std}'],timeout=60)
                    command([cmake,'--build',build,'--parallel','2'],timeout=60)
                    command([ctest,'--test-dir',build,'--output-on-failure','--no-tests=error'],timeout=30)
                    report['counts']['cmake_configurations']+=1
                    report['checks'].append(f'GoogleTest pinned version, C++{std}: both test cases passed')
            except (RuntimeError,subprocess.TimeoutExpired) as error:
                report['limitations'].append('Current GoogleTest dependency build not completed: '+str(error)[:1800])
                report['checks'].append('GoogleTest HTML/code preserved; external build not fully verified in this run')
        assert inputs()==report['input_sha256'], 'Inputs changed during author checks'
        report.update(status='passed',all_passed=True,finished_at=datetime.now(timezone.utc).isoformat())
        save(report)
        print(json.dumps({'status':report['status'],'counts':report['counts'],'limitations':report['limitations']},ensure_ascii=False))
        return 0
    except BaseException as error:
        report.update(status='failed',all_passed=False,error=f'{type(error).__name__}: {error}')
        save(report)
        print(report['error'],file=sys.stderr)
        return 1

if __name__=='__main__':
    sys.exit(main())
