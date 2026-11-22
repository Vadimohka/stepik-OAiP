#!/usr/bin/env python3
"""Syntax-check complete C++ programs as copied from current module 7--11 HTML.

This is not an execution test of the algorithms, and deliberately erroneous
examples remain erroneous. Related declarations are supplied only where the
lesson explicitly puts them in an earlier block or a named header.
"""
from concurrent.futures import ThreadPoolExecutor
import html
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).parent
LESSONS=[770590,770591,770592,770593,778425,778426,770588,770589,770594,770595,771129,771131,771130]


def blocks(sid):
    path=next((ROOT/'courses/86957/steps').rglob(f'*_{sid}_*.step'))
    text=json.loads(path.read_text())['block']['text']
    return [html.unescape(re.sub('<[^>]+>','',raw)) for raw in re.findall(r'<pre[^>]*>(.*?)</pre>',text,re.S)]


def main():
    units=[]
    for lesson in LESSONS:
        for path in sorted((ROOT/'courses/86957/steps'/str(lesson)).glob('*.step')):
            sid=int(path.stem.split('_')[1])
            for block,code in enumerate(blocks(sid),1):
                if re.search(r'\bint\s+main\s*\(',code):
                    units.append((sid,block,code))
    headers={'factorial.h':blocks(3212951)[1],
             'objects.h':blocks(3214991)[0],
             'interesting.hpp':blocks(3253429)[0]}

    def check(arg):
        sid,block,code,standard=arg
        context=[]
        if sid==3212949:
            code=blocks(3212949)[0]+'\n'+code
            context.append('Preceding sum definition from the same step')
        with tempfile.TemporaryDirectory(dir=OUT,prefix='syntax_') as temp:
            directory=Path(temp)
            for name in re.findall(r'#include\s+"([^"]+)"',code):
                assert name in headers
                (directory/name).write_text(headers[name]);context.append(name)
            source=directory/'example.cpp';source.write_text(code)
            command=['g++','-std='+standard,'-Wall','-Wextra','-pedantic-errors','-fsyntax-only',str(source)]
            result=subprocess.run(command,capture_output=True,text=True)
        expected_failure=(sid,block)==(3214973,1)
        assert (result.returncode != 0)==expected_failure,(sid,block,standard,result.stderr)
        return {'step_id':sid,'pre_block':block,'standard':standard,'scope':'syntax_only',
                'added_context':context,'expected_error_demo':expected_failure,'returncode':result.returncode,
                'diagnostics':re.sub(r'/[^\s:]+/syntax_[^\s:]+/example.cpp','example.cpp',result.stderr)}

    work=[(*unit,standard) for unit in units for standard in ('c++17','c++20')]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(check,work))
    report={'snapshot':'d936c0ee8d9f720ba26fec1b109a1153ae3b5930',
            'compiler':subprocess.run(['g++','--version'],capture_output=True,text=True).stdout.splitlines()[0],
            'complete_program_blocks':len(units),'compilations':len(results),
            'unexpected_failures':0,'runtime_not_tested':True,'results':results}
    (OUT/'cpp_snippet_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
