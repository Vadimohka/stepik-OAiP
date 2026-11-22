#!/usr/bin/env python3
"""Independent read-only QA of the root agent's eight revised module 1–4 code steps."""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import html
from itertools import permutations
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

WORK=Path(__file__).resolve().parent


def find_repo():
    for parent in Path(__file__).resolve().parents:
        if (parent/'courses/86957/steps').is_dir():
            return parent
    raise SystemExit('Cannot locate courses/86957/steps among the script parents; use --repo.')


p=argparse.ArgumentParser()
p.add_argument('--repo',type=Path)
p.add_argument('--out',type=Path,default=WORK/'foundations_peer_root.json')
args=p.parse_args()
args.repo=(args.repo or find_repo()).resolve()
ids={3262772,3262735,3264578,3269060,3281279,3281287,3177655,4643238}
files={}
for f in (args.repo/'courses/86957/steps').glob('*/*.step'):
    sid=int(f.name.split('_')[1])
    if sid in ids:files[sid]=f
assert set(files)==ids
blocks={s:json.loads(f.read_text())['block'] for s,f in files.items()}
hashes={s:hashlib.sha256(f.read_bytes()).hexdigest() for s,f in files.items()}
results=[]


def decimal_text(value):
    with localcontext() as c:
        c.prec=90
        return str(Decimal(value.numerator)/Decimal(value.denominator))


def oracle(sid,data):
    if sid==4643238:
        return '0'
    if sid==3262772:
        first=Fraction(data)
        ratio=Fraction(1,1001)
        return decimal_text(first/(1-ratio))
    if sid==3262735:
        first,last=map(Fraction,data.split())
        difference=(last-first)/99
        total=sum((first+n*difference for n in range(70)),Fraction(0))
        return decimal_text(difference)+'\n'+decimal_text(total)
    if sid==3264578:
        x,y=map(int,data.split())
        if x==0 and y==0:return 'ERROR'
        return 'YES' if (y!=0 and x%y==0) or (x!=0 and y%x==0) else 'NO'
    if sid==3269060:
        sides=sorted(map(Fraction,data.split()))
        return 'YES' if sides[0]+sides[1]>sides[2] else 'NO'
    if sid==3281279:
        a,b,c,x,y=map(Fraction,data.split())
        if min(a,b,c,x,y)<=0:return 'Incorrect input'
        return 'YES' if any(u<=x and v<=y for u,v,_ in permutations((a,b,c))) else 'NO'
    if sid==3281287:
        k=int(data)
        ending='грибов' if 11<=k%100<=14 else ('гриб' if k%10==1 else 'гриба' if 2<=k%10<=4 else 'грибов')
        return f'Мы нашли {k} {ending} в лесу'
    if sid==3177655:
        k=int(data)
        return '\n'.join(' '.join(str(i*j) for j in range(1,k)) for i in range(1,k))
    raise AssertionError(sid)


checks={}
for sid,b in blocks.items():
    # These checker bodies were inspected before execution: only local parsing,
    # Decimal arithmetic, regex validation and string comparison; no I/O/network.
    scope={}
    exec(compile(b['source']['code'],f'<reviewed checker {sid}>','exec'),scope)
    checks[sid]=scope['check']
    tests=b['source']['test_cases']
    for i,(data,clue) in enumerate(tests,1):
        expected=oracle(sid,data)
        assert checks[sid](expected,clue),(sid,i,'independent answer rejected',expected,clue)
        if sid not in {3262772,3262735,3177655}:
            assert expected==clue.strip(),(sid,i,'clue mismatch')
        elif sid==3177655:
            assert expected.split()==clue.split(),(sid,i,'table mismatch')
        else:
            tolerance=Fraction('1e-7' if sid==3262772 else '1e-9')
            for a,c in zip(expected.split(),clue.split()):
                a,c=Fraction(a),Fraction(c)
                assert abs(a-c)<=max(tolerance,tolerance*abs(a)),(sid,i,'clue outside numeric tolerance')
        if sid==4643238:
            assert not checks[sid]('1',clue)
    assert b['options']['samples']==tests[:b['source']['samples_count']],(sid,'sample/source divergence')
    results.append({'step_id':sid,'stored_tests':len(tests),'independent_oracle':'passed'})

rejections=[]
for sid in (3262772,3262735):
    count=1 if sid==3262772 else 2
    for data,clue in blocks[sid]['source']['test_cases']:
        tokens=oracle(sid,data).split()
        assert len(tokens)==count
        for i in range(count):
            for bad in ('NaN','sNaN','inf','-Infinity','1_0','not_a_number','1e9999999'):
                attempt=tokens.copy();attempt[i]=bad
                assert not checks[sid](' '.join(attempt),clue),(sid,'bad number accepted',bad)
            value=Fraction(tokens[i])
            t=Fraction('1e-7' if sid==3262772 else '1e-9')
            attempt=tokens.copy();attempt[i]=decimal_text(value+max(t,t*abs(value))*4)
            assert not checks[sid](' '.join(attempt),clue),(sid,'outside tolerance accepted')
        assert not checks[sid](' '.join(tokens+['0']),clue)
        assert not checks[sid](' '.join(tokens[:-1]),clue)
        assert checks[sid]('\n\t'.join(tokens)+'\n',clue)
    rejections.append({'step_id':sid,'nonfinite_malformed_token_count_and_wrong_numeric_rejection':'passed'})

for data,clue in blocks[3177655]['source']['test_cases']:
    table=oracle(3177655,data)
    assert checks[3177655](table.replace(' ','\t'),clue)
    tokens=table.split();tokens[-1]=str(int(tokens[-1])+1)
    assert not checks[3177655](' '.join(tokens),clue)
    assert not checks[3177655](table+' 0',clue)

extra={
  3264578:{'0 -2':'YES','-2 0':'YES','0 0':'ERROR','-7 7':'YES','7 3':'NO'},
  3281279:{'1 2 3 2 1':'YES','1 2 3 1 1':'NO','1 2 3 0 1':'Incorrect input','1 2 3 -1 1':'Incorrect input','2 3 1 1 2':'YES'},
}
for sid,cases in extra.items():
    for data,expected in cases.items():
        assert oracle(sid,data)==expected

# Compile and run only the inspected standard I/O template from the table example.
template=blocks[3177655]['source']['templates_data'].split('\n',1)[1]
cpp=WORK/'cpp'/'peer_table_3177655.cpp'
cpp.parent.mkdir(parents=True,exist_ok=True)
cpp.write_text(template+'\n')
build=tempfile.TemporaryDirectory(prefix='build-peer-',dir=WORK)
exe=Path(build.name)/'peer_table_3177655'
compiler=shutil.which('g++')
assert compiler, 'g++ is required for the multiplication-table check'
command=['g++','-std=c++17','-Wall','-Wextra','-pedantic',str(cpp.relative_to(WORK)),'-o',str(exe.relative_to(WORK))]
subprocess.run(command,cwd=WORK,check=True,capture_output=True,text=True,timeout=30)
for k in (2,4,10,100):
    r=subprocess.run([str(exe)],input=str(k),capture_output=True,text=True,check=True,timeout=5)
    assert r.stdout.split()==oracle(3177655,str(k)).split(),k
assert hashes=={s:hashlib.sha256(f.read_bytes()).hexdigest() for s,f in files.items()}
report={'status':'passed','steps':results,'numeric_negative_checks':rejections,
        'total_stored_tests':sum(r['stored_tests'] for r in results),
        'extra_zero_and_dimension_cases':extra,
        'table_template':{'command':command,'sizes':[2,4,10,100],'status':'passed'},
        'files_unchanged':True,'step_sha256':hashes,'regressions':[],
        'notes':['3177655 compares token order and ignores whitespace, including line boundaries; the supplied template formats rows as requested.',
                 'The C-only availability of 4643238 is a step setting retained intentionally; its mathematical identity is exact.']}
args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
build.cleanup()
print(json.dumps({'status':'passed','steps':len(results),'stored_tests':report['total_stored_tests'],'report':args.out.name},ensure_ascii=False))
