#!/usr/bin/env python3
"""Independent references and regression checks for the second course revision.

Only reviewed graders are loaded. The single reviewed generated-task solver is
executed explicitly below. No network or live Stepik interaction is performed.
"""
from __future__ import annotations

import ast
import collections
import hashlib
import itertools
import json
import math
import random
import subprocess
import tempfile
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

from verify_revised_steps import BLOCKS, ROOT, cases, checker

RECORDS = []


def record(name, **details):
    RECORDS.append(dict(check=name, passed=True, **details))


def check_cases(sid, solve):
    for index, (data, clue) in enumerate(cases(sid), 1):
        answer = solve(data)
        if not checker(sid)(answer, clue):
            raise AssertionError((sid, index, answer[:300], str(clue)[:300]))
    record('independent_reference', step_id=sid, datasets=len(cases(sid)))


def check_numeric():
    for sid, count in [(3262772, 1), (3262735, 2)]:
        check = checker(sid)
        for data, clue in cases(sid):
            numbers = list(map(Fraction, data.split()))
            if sid == 3262772:
                expected = [numbers[0] * Fraction(1001, 1000)]
            else:
                first, hundredth = numbers
                difference = (hundredth - first) / 99
                expected = [difference, sum(first + i * difference for i in range(70))]
            with localcontext() as ctx:
                ctx.prec = 60
                exact = [Decimal(x.numerator) / Decimal(x.denominator) for x in expected]
                answer = ' '.join(format(x, '.45g') for x in exact)
                assert check(answer, clue), (sid, data, answer, clue)
                assert check(' \n' + '\t'.join(format(x, '.30e') for x in exact) + '\n', clue)
                wrong = exact[:]
                wrong[-1] += max(Decimal(1), abs(wrong[-1])) / 100
                assert not check(' '.join(str(x) for x in wrong), clue)
            for bad in ['NaN', 'inf', '-Infinity', '1e9999999999999999999', 'hello', '', '1_000']:
                assert not check(' '.join([bad] * count), clue), (sid,bad)
            assert not check(clue + ' 0', clue)
            if count == 2: assert not check(clue.split()[0], clue)
        record('numeric_values_and_negative_controls', step_id=sid, datasets=len(cases(sid)))


def local_min(data):
    it=iter(map(int,data.split())); rows,cols=next(it),next(it)
    values=list(it); assert len(values)==rows*cols
    assert 1<=rows<=1000 and 1<=cols<=1000 and rows*cols<=10**5
    assert all(abs(x)<=10**9 for x in values)
    count=0
    for i in range(rows):
        for j in range(cols):
            neighbors=[values[r*cols+c] for r in range(max(0,i-1),min(rows,i+2))
                       for c in range(max(0,j-1),min(cols,j+2)) if (r,c)!=(i,j)]
            count += all(values[i*cols+j]<x for x in neighbors)
    return str(count)


def prefix_max(data):
    it=iter(map(int,data.split())); n,m=next(it),next(it);v=list(it)
    assert len(v)==n*m and 1<=n*m<=10**5 and all(abs(x)<=10**9 for x in v)
    return ' '.join(str(max(v[r*m+c] for r in range(i+1) for c in range(j+1)))
                    for i in range(n) for j in range(m))


def digit_positions(data):
    number,index=data.split();index=int(index);reverse=number[::-1]
    assert number.isdigit() and number[0]!='0' and 1<=len(number)<=32767 and 0<=index<len(number)
    digit=reverse[index]
    return f'{len(set(number))}\n{digit}\n'+' '.join(str(i) for i,ch in enumerate(reverse) if ch==digit)


def replace_between(data):
    a=list(map(int,data.split()));assert 1<=len(a)<=10**5 and all(abs(x)<=10**9 for x in a)
    lo=a.index(min(a));hi=a.index(max(a));lo,hi=min(lo,hi),max(lo,hi)
    result=[0 if lo<i<hi else x for i,x in enumerate(a)]
    if result.count(0)*2>len(result): result=[x for x in result if x!=0]
    return ' '.join(map(str,result))


def matrix_product(data):
    it=iter(map(int,data.split()));n=next(it);a=[[next(it) for _ in range(n)] for _ in range(n)]
    m=next(it);b=[[next(it) for _ in range(m)] for _ in range(m)]
    assert list(it)==[] and n==m and 1<=n<=100
    assert all(abs(x)<=10**6 for row in a+b for x in row)
    return '\n'.join(' '.join(str(sum(x*y for x,y in zip(row,column))) for column in zip(*b)) for row in a)


def characteristic(data):
    fields=data.split();m,n=map(int,fields[:2]);assert len(fields)==2+m+n
    with localcontext() as ctx:
        ctx.prec=650
        a,b=list(map(Decimal,fields[2:2+m])),list(map(Decimal,fields[2+m:]))
        assert 2<=m<=10**5 and 2<=n<=10**5
        assert all(x.is_finite() and abs(x)<=Decimal('1e308') for x in a+b)
        # Sum each difference exactly, independently of the telescoping shortcut.
        ca=sum(x-y for x,y in zip(a,a[1:]));cb=sum(x-y for x,y in zip(b,b[1:]))
        return '1' if ca>=cb else '2'


def f(n):
    while n and n%10==0: n//=10
    return n%10


def prefix_f(n):
    if n<0: return 0
    total=0
    while n:
        quotient,last=divmod(n,10)
        total += 45*quotient+last*(last+1)//2
        n=quotient
    return total


def sums_f(data):
    result=[]
    for line in data.splitlines():
        p,q=map(int,line.split())
        if p<0 and q<0: break
        assert 0<=p<=q<=2147483647
        result.append(str(prefix_f(q)-prefix_f(p-1)))
    return '\n'.join(result)


def power_last_ten(data):
    it=iter(map(int,data.split()));t=next(it);result=[]
    for _ in range(t):
        n,m=next(it),next(it);assert 0<=n<=10**9 and 0<=m<=10**9
        modulus=10**10
        residue=pow(n,m,modulus)
        capped=1;base=n;exponent=m
        while exponent:
            if exponent&1: capped=min(modulus,capped*base)
            base=min(modulus,base*base);exponent//=2
        result.append(str(residue) if capped<modulus else f'{residue:010d}')
    assert not list(it)
    return '\n'.join(result)


def chip(data):
    lines=data.splitlines();q=int(lines[0]);assert len(lines)==1+2*q;answers=[]
    assert sum(len(s) for s in lines[1::2])<=500
    for s,t in zip(lines[1::2],lines[2::2]):
        found=False
        for start in range(len(s)):
            for right in range(min(len(t),len(s)-start)):
                end=start+right;left=len(t)-right-1
                if end-left<0: continue
                generated=s[start:end+1]+s[end-left:end][::-1]
                if generated==t: found=True;break
            if found:break
        answers.append('YES' if found else 'NO')
    return '\n'.join(answers)


def reform(data):
    s=''.join(ch for ch in data if ch not in 'CQWX');out=[];i=0
    rules={'ph':'f','th':'z','ee':'i','qu':'kv','you':'u','oo':'u'}
    while i<len(s):
        for old,new in rules.items():
            if s[i:i+len(old)].lower()==old:
                out.append(new.capitalize() if s[i].isupper() else new);i+=len(old);break
        else:out.append(s[i]);i+=1
    s=''.join(out);out=[]
    for ch in s:
        replacement={'q':'k','x':'ks','w':'v'}.get(ch.lower(),ch)
        out.append(replacement.capitalize() if ch.isupper() else replacement)
    s=''.join(out);out=[]
    for i,ch in enumerate(s):
        if ch.lower()=='c':
            replacement='s' if i+1<len(s) and s[i+1].lower() in 'eiy' else 'k'
            out.append(replacement.upper() if ch.isupper() else replacement)
        else:out.append(ch)
    result=[]
    for ch in ''.join(out):
        if result and ch.lower()==result[-1].lower() and ch.lower() in 'bcdfghjklmnpqrstvwxz': continue
        result.append(ch)
    return ''.join(result)


def roman(data):
    n=int(data);assert 1<=n<=3999
    units=['','I','II','III','IV','V','VI','VII','VIII','IX']
    tens=['','X','XX','XXX','XL','L','LX','LXX','LXXX','XC']
    hundreds=['','C','CC','CCC','CCCC','CCCCC','CCCCM','CCCM','CCM','CM']
    return 'M'*(n//1000)+hundreds[n//100%10]+tens[n//10%10]+units[n%10]


def substring_pairs(s):
    # Each suffix-automaton state represents an interval of substring lengths;
    # all those substrings have the same occurrence count.
    transitions=[{}];link=[-1];length=[0];count=[0];last=0
    for ch in s:
        current=len(length);length.append(length[last]+1);count.append(1);transitions.append({});link.append(0)
        p=last
        while p>=0 and ch not in transitions[p]: transitions[p][ch]=current;p=link[p]
        if p>=0:
            q=transitions[p][ch]
            if length[p]+1==length[q]: link[current]=q
            else:
                clone=len(length);length.append(length[p]+1);count.append(0)
                transitions.append(transitions[q].copy());link.append(link[q])
                while p>=0 and transitions[p].get(ch)==q: transitions[p][ch]=clone;p=link[p]
                link[q]=link[current]=clone
        last=current
    answer=0
    for state in sorted(range(1,len(length)),key=length.__getitem__,reverse=True):
        answer += count[state]*(count[state]-1)//2*(length[state]-length[link[state]])
        count[link[state]]+=count[state]
    return answer


def pair_datasets(data):
    lines=data.splitlines();assert len(lines)==1+int(lines[0])
    assert all(1<=len(s)<=10**5 and all('a'<=ch<='z' for ch in s) for s in lines[1:])
    return '\n'.join(str(substring_pairs(s)) for s in lines[1:])


def bidecimal_prefix(wanted):
    # Build decimal strings from the least significant digit, allowing temporary
    # leading zeroes. Retain exactly those matching their low binary bits.
    candidates=[(0,0)];answers=[];power10=1;power2=1
    while len(answers)<wanted:
        expanded=[];fresh=[]
        for decimal,binary in candidates:
            for digit in [0,1]:
                new_decimal=decimal+digit*power10;new_binary=binary+digit*power2
                if new_decimal % (power2*2)==new_binary:
                    expanded.append((new_decimal,new_binary))
                    if digit:fresh.append(new_decimal)
        answers.extend(sorted(fresh));candidates=expanded;power10*=10;power2*=2
    return answers


def check_generated_tasks():
    check=checker(4927308)
    square='4 9 2\n3 5 7\n8 1 6'
    assert check(square,3) and check(square+'\n',3)
    shifted='\n'.join(' '.join(str(int(x)*2-50) for x in row.split()) for row in square.splitlines())
    assert check(shifted,3) and check('-10',1) and check('NO',2)
    for bad in ['1 1 1\n1 1 1\n1 1 1','1 5 9\n6 7 2\n8 3 4','4 9 2\n3 5 7','NO','4.0 9 2\n3 5 7\n8 1 6']:
        assert not check(bad,3)
    assert not check('1 2\n3 4',2)
    tree=ast.parse(BLOCKS[4927308]['source']['code'])
    generated=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)))
    assert len(generated)==14 and all(1<=int(data)<=1500 and int(data)==clue for data,clue in generated)
    record('magic_square_custom_checker',step_id=4927308,generated_sizes=len(generated),positive_cases=5,negative_cases=6)

    # Source manually reviewed: it imports random and defines generate, solve,
    # check, with no top-level actions. Run its solver only on small graphs.
    namespace={};exec(compile(BLOCKS[4738986]['source']['code'],'reviewed-route-task','exec'),namespace)
    rng=random.Random(86957)
    def brute(data):
        v=list(map(int,data.split()));n,m,k=v[:3];edges=v[3::2];colors=v[4::2];strings=[]
        for start in range(n):
            at=start;word=[]
            for _ in range(m):word.append(str(colors[at]));at=edges[at]-1
            strings.append(''.join(word))
        return sorted(strings)[k-1]
    check_cases(4738986,brute)
    random_cases=[]
    for _ in range(16):
        n=rng.randint(1,8);m=rng.randint(1,12);k=rng.randint(1,n)
        data=f'{n} {m} {k}\n'+'\n'.join(f'{rng.randint(1,n)} {rng.randint(1,3)}' for _ in range(n))
        assert namespace['solve'](data)==brute(data)
        random_cases.append((n,m,k))
    random_state=random.getstate()
    try:
        random.seed(86957)
        generated=namespace['generate']()
    finally:random.setstate(random_state)
    colors=set();destinations=set()
    for data in generated:
        v=list(map(int,data.split()));n,m,k=v[:3]
        assert len(v)==3+2*n and 1<=k<=n<=100000 and 1<=m<=100000
        assert all(1<=x<=n for x in v[3::2]) and all(1<=x<=3 for x in v[4::2])
        colors.update(v[4::2]);destinations.update(v[3::2])
    assert colors=={1,2,3} and 100000 in destinations
    record('route_solver_and_generator',step_id=4738986,small_graph_comparisons=len(random_cases),generated_datasets=len(generated),colors=sorted(colors))


def check_cpp():
    source=ROOT/'imports/86957/validation/round2_solutions.cpp'
    compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0]
    runs=0;details=[]
    with tempfile.TemporaryDirectory(prefix='round2-cpp-',dir=ROOT/'imports/86957') as tmp:
        binary=Path(tmp)/'reference'
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-pedantic-errors','-O2',str(source),'-o',str(binary)],check=True,capture_output=True,text=True,timeout=30)
        for sid in [3262772,3262735,3264578,3269060,3281279,3281287,3177655,3384444,3382745,3383135]:
            precisions=[8,17] if sid==3262772 else [10,17] if sid==3262735 else [17]
            for precision in precisions:
                for index,(data,clue) in enumerate(cases(sid),1):
                    run=subprocess.run([str(binary),str(sid),str(precision)],input=data,text=True,capture_output=True,check=True,timeout=3)
                    assert checker(sid)(run.stdout,clue),(sid,index,run.stdout,clue)
                    runs+=1
            details.append(dict(step_id=sid,datasets=len(cases(sid)),precisions=precisions))
        # Also exercise the actual multiplication example supplied to learners.
        template=BLOCKS[3177655]['options']['code_templates']['c++']
        template_source=Path(tmp)/'multiplication.cpp';template_source.write_text(template)
        template_binary=Path(tmp)/'multiplication'
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-pedantic-errors',str(template_source),'-o',str(template_binary)],check=True,capture_output=True,text=True,timeout=30)
        for data,clue in cases(3177655):
            run=subprocess.run([str(template_binary)],input=data,text=True,capture_output=True,check=True,timeout=3)
            assert checker(3177655)(run.stdout,clue)
    record('compiled_cpp_reference_solutions',compiler=compiler,standard='c++17',runs=runs,results=details,learner_template_runs=len(cases(3177655)))


def main():
    check_numeric()
    for sid,solve in [(3341723,local_min),(3381234,prefix_max),(3381291,digit_positions),
                      (3382745,replace_between),(3383135,matrix_product),(4672519,characteristic),
                      (4700299,lambda data:'1.'+'9'*(int(data)-1)+'8'),(3428206,sums_f),
                      (4739135,power_last_ten),(3253164,lambda data:str((int(data)+1)//10)),
                      (3446132,chip),(4949336,reform),(3496771,roman)]:
        check_cases(sid,solve)
    for n in range(500): assert prefix_f(n)==sum(f(i) for i in range(n+1))
    record('recursive_sum_reference_crosscheck',small_values=500)
    for sid in [3177655,3384444,3381291,3382745,3383135]:
        check=checker(sid)
        for _,clue in cases(sid):
            assert check(' \n'+'\t'.join(clue.split())+' \n',clue)
            assert not check(clue+' 99999999999999999999',clue)
            if clue.split(): assert not check(' '.join(clue.split()[:-1]),clue)
        record('numeric_token_whitespace_and_negative_controls',step_id=sid,datasets=len(cases(sid)))
    for data,_ in cases(5822035):
        v=data.split();assert len(v)==1+int(v[0]);words=v[1:]
        assert sum(map(len,words))<=10**5
        assert all(s.isdigit() and (s=='0' or s[0]!='0') for s in words)
    record('salary_input_limits',step_id=5822035,datasets=len(cases(5822035)))
    for size in range(1,9):
        for s in map(''.join,itertools.product('ab',repeat=size)):
            counter=collections.Counter(s[i:j] for i in range(size) for j in range(i+1,size+1))
            expected=sum(n*(n-1)//2 for n in counter.values())
            assert substring_pairs(s)==expected,(s,expected)
    record('suffix_automaton_against_exhaustive_substring_count',strings=510)
    check_cases(4734985,pair_datasets)
    sequence=bidecimal_prefix(10000)
    assert sequence[:6]==[1,10,11,100,101,110]
    for n in sequence:
        assert bin(n)[2:].endswith(str(n))
    check_cases(3496826,lambda data:str(sequence[int(data)-1]))
    record('bidecimal_sequence_membership',values=10000)
    check_generated_tasks()
    check_cpp()
    reviewed=[p for p in (ROOT/'courses/86957/steps').glob('*/*_code.step')]
    output=ROOT/'imports/86957/validation/round2_code_validation.json'
    payload=dict(course_id=86957,scope='Second-pass local grading and reference verification; no live Stepik run.',
                 all_passed=True,check_count=len(RECORDS),checks=RECORDS,
                 code_file_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(reviewed)})
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(all_passed=True,check_count=len(RECORDS),output=str(output.relative_to(ROOT)))))


if __name__=='__main__':
    main()
