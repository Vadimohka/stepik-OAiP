#!/usr/bin/env python3
"""Author checks for T6 theory: exact HTML bindings and algorithm invariants."""
from pathlib import Path
import hashlib, html, json, re, subprocess, tempfile

HERE=Path(__file__).resolve().parent
PACKAGE=HERE.parent.parent
ROOT=PACKAGE.parents[2]
REPORT=HERE/'validation.json'

def codes(sid):
    path=next((PACKAGE/'steps').glob(f'*/*_{sid}_text.step'))
    body=json.loads(path.read_text())['block']['text']
    return [html.unescape(x).strip() for x in re.findall(r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>',body,re.S)]

BINDINGS={4035563:['queue.cpp'],4036909:['deque.cpp'],4047616:['static_cast.cpp'],
          4047627:['dynamic_cast.cpp'],4047680:['const_cast.cpp'],4047681:['representation.cpp'],
          3570230:['bst.cpp'],3570281:['avl.hpp','avl_demo.cpp'],
          3570332:['ordered_iteration.cpp'],4035481:['hash_table.hpp','hash_demo.cpp']}
EXPECTED={'queue.cpp':'parse\nsave\n','deque.cpp':'20 30\n10 20 30 40 \n',
          'static_cast.cpp':'3.5 42\n','dynamic_cast.cpp':'3\nnot a circle\nnot a circle\nreference cast failed\n',
          'const_cast.cpp':'12\n7\n','bst.cpp':'false root\n10 20 30\n',
          'avl_demo.cpp':'20 3\n10:10 30:30 40:40 \n',
          'hash_demo.cpp':'3 0.75\nbook\n2 8\nfalse\n',
          'ordered_iteration.cpp':'10:A 20:B 30:C \n30\n',
          'rbt_demo.cpp':'20\nfalse false true\n'}

def run(args,timeout=30):
    result=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if result.returncode:
        raise RuntimeError('Command failed: '+' '.join(args)+'\n'+result.stdout+result.stderr)
    return result.stdout

report={'status':'running','passed':False,'standards':['c++17','c++20'],'checks':[]}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
try:
    journal=json.loads((PACKAGE/'changes_t6.json').read_text())
    assert len(journal)==27 and len({x['step_id'] for x in journal})==27
    for item in journal:
        baseline=PACKAGE/'baseline'/item['path']
        if not baseline.is_file(): baseline=ROOT/'courses/86957'/item['path']
        before=json.loads(baseline.read_text())
        after=json.loads((PACKAGE/item['path']).read_text())
        assert before['block']['name']==after['block']['name']=='text'
        assert before['block']['text']!=after['block']['text']
        before['block']['text']=after['block']['text']
        assert before==after, f'Non-theory field changed: {item["step_id"]}'
    for sid,names in BINDINGS.items():
        assert codes(sid)==[(HERE/name).read_text().strip() for name in names],f'Code mismatch: {sid}'
    rb='#pragma once\n'+'\n\n'.join([codes(3570303)[1]]+codes(3570304)+codes(3570333))+'\n'
    assert rb==(HERE/'rbt.hpp').read_text(), 'RB assembled header differs from lesson blocks'
    report['checks'].append({'kind':'identity_and_html_code_binding','steps':27,'passed':True})
    compiles=0; executions=0
    with tempfile.TemporaryDirectory(prefix='t6-check-') as tmp:
        for standard in report['standards']:
            for src in sorted(HERE.glob('*.cpp')):
                binary=str(Path(tmp)/(standard+'-'+src.stem))
                run(['g++','-std='+standard,'-Wall','-Wextra','-Wpedantic','-Werror',
                     '-O1','-g','-fsanitize=undefined','-fno-sanitize-recover=all',str(src),'-o',binary])
                compiles+=1
                output=run([binary],timeout=30); executions+=1
                if src.name in EXPECTED: assert output==EXPECTED[src.name],(src.name,output)
                elif src.name=='representation.cpp':
                    lines=output.splitlines(); n=int(lines[0]); values=list(map(int,lines[1].split()))
                    assert len(values)==n and any(values)
                elif src.name=='invariants.cpp':
                    assert output.startswith('verified states: ')
                else: raise AssertionError('Unspecified example: '+src.name)
                report['checks'].append({'source':src.name,'standard':standard,'output':output,'passed':True})
    files=[PACKAGE/x['path'] for x in journal]+list(HERE.glob('*.cpp'))+list(HERE.glob('*.hpp'))+[Path(__file__),PACKAGE/'changes_t6.json']
    report.update(status='passed',passed=True,compiler=run(['g++','--version']).splitlines()[0],
                  compilation_count=compiles,execution_count=executions,
                  input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))},
                  limits=['Конечные авторские проверки не являются доказательством для всех состояний.',
                          'UndefinedBehaviorSanitizer использован; ThreadSanitizer и проверка многопоточности не требуются для однопоточных примеров.',
                          'Число байтов и порядок представления unsigned int намеренно не зафиксированы как переносимый вывод.'])
except Exception as error:
    report.update(status='failed',passed=False,error=str(error))
    raise
finally:
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','compilation_count','execution_count']},ensure_ascii=False))
