#!/usr/bin/env python3
"""Focused checks for corrected module 5–10 steps; no course generators are run.

Only explicitly selected, manually reviewed safe C/C++ fragments are compiled.
The two changed checker functions are extracted without executing their module,
solve(), or generate(). Numerical task references are implemented independently.
"""
import argparse
import ast
import copy
import hashlib
import html
import itertools
import json
import re
import string
import subprocess
import tempfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO_CANDIDATES=[HERE.parent/'stepik-course-fixes',*HERE.parents,Path.cwd()]
DEFAULT_REPO=next((p for p in REPO_CANDIDATES if (p/'courses/86957/steps').is_dir()),Path.cwd())
CHANGED_STEP_IDS={
    3177298,3212907,3212920,3212928,3212935,3212937,3212947,3212950,3212951,
    3212968,3212969,3212970,3212990,3212991,3213003,3213208,3213210,3213242,
    3213247,3213256,3214845,3214901,3214903,3214904,3214909,3214910,3214911,
    3214972,3215024,3215177,3215179,3215192,3252940,3253129,3253503,3253553,
    3324082,3324316,3330670,3330738,3332379,3333775,3381234,3383209,3384518,
    3404721,3404829,3404927,3408471,3408767,3408864,3408968,3426151,3428470,
    3428716,3428845,3435399,3437788,3446002,3446094,4700299,4717782,4717787,
    4718299,4738986,4739135,
}
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,default=DEFAULT_REPO)
parser.add_argument('--compiler',default='g++')
parser.add_argument('--c-compiler',default='gcc')
parser.add_argument('--output',type=Path,default=HERE/'core_validation.json')
parser.add_argument('--examples',type=Path,default=HERE/'core-validation')
args=parser.parse_args()
ROOT=args.repo.resolve(); OUT=args.output; EXAMPLES=args.examples
EXAMPLES.mkdir(parents=True,exist_ok=True)
baseline=json.loads((HERE/'core_before.json').read_text()) if (HERE/'core_before.json').exists() else None
findings=json.loads((ROOT/'audit/findings.json').read_text())['findings']
assigned=[f for f in findings if 5<=f['module']<=10]
course=json.loads((ROOT/'courses/86957/course.json').read_text())
sections={s['id']:s['position'] for s in course['sections']}
modules={u['lesson']:sections[u['section']] for u in course['units']}
paths={int(p.name.split('_')[1]):p for p in (ROOT/'courses/86957/steps').rglob('*.step') if 5<=modules[int(p.parent.name)]<=10}
steps={sid:json.loads(p.read_text()) for sid,p in paths.items()}
report={'scope':'Corrected .step files in modules 5–10','checks':[],'compilations':[],'limitations':[
    'No live Stepik submissions or server-side preprocessing were exercised.',
    'The Google Test syntax probe uses a minimal two-argument macro, not an installed Google Test runner.',
    'Only explicitly selected safe fragments are executed; no course generator or full exported checker module is executed.',
    'Examples with signed-char narrowing assume C++20 and the checked 8-bit-char environment.',
    'The missing image in step 3214901 was removed without reconstructing unknown original content.'
]}
def checked(name,**data):report['checks'].append({'name':name,'passed':True,**data})
def b(sid):return steps[sid]['block']
def snippets(sid):return [html.unescape(re.sub('<[^>]*>','',x)) for x in re.findall(r'<pre\b[^>]*>.*?</pre>',b(sid)['text'],re.S)]
def snippet(sid,needle):
    found=[x for x in snippets(sid) if needle in x]
    assert len(found)==1,(sid,needle,len(found));return found[0]
def op(sid,needle):
    found=[x for x in b(sid)['source']['options'] if needle in html.unescape(x['text'])]
    assert len(found)==1,(sid,needle,len(found));return found[0]

# Structure and exact grading keys.
if baseline:
    changed=[sid for sid,d in steps.items() if d!=baseline[str(sid)]]
    for sid in changed:
        assert steps[sid]['id']==baseline[str(sid)]['id']
        assert steps[sid]['time']==baseline[str(sid)]['time']
        assert set(steps[sid])==set(baseline[str(sid)])=={'id','time','block'}
        assert b(sid)['name']==baseline[str(sid)]['block']['name']
    checked('import_envelopes_preserved',changed_step_count=len(changed),step_ids=sorted(changed))
else:
    changed=sorted(CHANGED_STEP_IDS)
    checked('scope_files_parsed',step_count=len(steps),note='Baseline not supplied; exact original envelope comparison skipped.')

class Tags(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.tags=[]
    def handle_starttag(self,tag,attrs):self.tags.append(tag)
allowed={'p','br','b','strong','i','em','code','pre','span','sup','sub','a','u','s','div','ul','ol','li','table','thead','tbody','tr','td','th'}
choice_count=0
for sid in changed:
    text=b(sid)['text']
    assert not any(ord(ch)<32 and ch not in '\n\r\t' for ch in text),sid
    if b(sid)['name']=='choice':
        src=b(sid)['source']; opts=src['options']; good=sum(o['is_correct'] for o in opts)
        assert good>=1 and src['sample_size']<=len(opts),sid
        assert src['is_multiple_choice']==b(sid)['options']['is_multiple_choice'],sid
        if not src['is_multiple_choice']:assert good==1,sid
        if src.get('is_html_enabled'):
            for o in opts:
                tags=Tags();tags.feed(o['text']);assert set(tags.tags)<=allowed,(sid,tags.tags)
        choice_count+=1
    if b(sid)['name']=='code':
        src=b(sid)['source']; ast.parse(src['code'])
        assert b(sid)['options']['samples']==src['test_cases'][:src['samples_count']],sid
checked('choice_and_code_schema',choice_count=choice_count)

assert op(3330670,'mat[0][3] даст UB')['is_correct']
assert not op(3330670,'mat[0][3] даст 4')['is_correct']
assert op(3330670,'int mat[][2] = {1, 2, 3};')['is_correct']
assert not op(3330738,'new int[2]{1, 2} - 1')['is_correct']
assert op(3330738,'int* a = new int[2]; delete a;')['is_correct']
assert op(3330738,'new char[]{"Hello"}')['is_correct']
assert not op(3332379,'delete b;')['is_correct']
assert op(3332379,'После delete разыменование')['is_correct']
assert op(3428470,'Неопределённое поведение')['is_correct']
assert op(4717787,'косвенного обращения')['is_correct']
assert op(3435399,'C-строку можно копировать memcpy')['is_correct']
assert op(3408767,'Существуют алгоритмы сортировки слиянием')['is_correct']
assert not op(3408767,'Любой алгоритм сортировки слиянием')['is_correct']
assert op(3408864,'независимых равномерно распределённых')['is_correct']
fill=b(3408968)['source'];assert fill['components'][3]['options']==[{'text':'strpbrk','is_correct':True}]
assert 'strprbk' not in b(3214845)['text']
assert 'lh7-us.googleusercontent.com' not in b(3214901)['text']
checked('targeted_grading_keys',steps=[3330670,3330738,3332379,3428470,4717787,3435399,3408767,3408864,3408968])

def isolated_check(sid):
    parsed=ast.parse(b(sid)['source']['code'])
    nodes=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='check']
    assert len(nodes)==1
    # Inspection of this allowlist excludes IO and arbitrary imported code.
    for node in ast.walk(nodes[0]):
        if isinstance(node,ast.Call):
            assert (isinstance(node.func,ast.Name) and node.func.id=='str') or (isinstance(node.func,ast.Attribute) and node.func.attr in {'strip','rstrip','split'}),ast.dump(node)
    ns={'__builtins__':{'str':str}}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),f'step_{sid}_check_only','exec'),ns)
    def accept(reply,clue):
        value=ns['check'](reply,clue)
        return value[0] if isinstance(value,tuple) else bool(value)
    return accept

matrix_check=isolated_check(3381234)
positive=negative=0
for dataset,clue in b(3381234)['source']['test_cases']:
    numbers=list(map(int,dataset.split()));r,c=numbers[:2];a=[numbers[2+i*c:2+(i+1)*c] for i in range(r)]
    expected=[max(a[x][y] for x in range(i+1) for y in range(j+1)) for i in range(r) for j in range(c)]
    tokens=clue.split();assert list(map(int,tokens))==expected
    for reply in [clue,clue+'\n',clue+'\r\n',' '.join(tokens),'\n\t'.join(tokens),'  '+' '.join(tokens)+'  ']:
        assert matrix_check(reply,clue);positive+=1
    wrong=tokens.copy();wrong[0]=str(int(wrong[0])+1)
    for reply in [' '.join(wrong),' '.join(tokens[:-1]),' '.join(tokens+['0']),'wrong']:
        assert not matrix_check(reply,clue);negative+=1
checked('matrix_checker_regression',positive=positive,negative=negative,test_cases=5)

digit_check=isolated_check(4738986);positive=negative=0
for dataset,clue in b(4738986)['source']['test_cases']:
    t=list(map(int,dataset.split()));n,m,k=t[:3];links=t[3::2];colors=t[4::2]
    candidates=[]
    for start in range(n):
        cur=start;out=[]
        for _ in range(m):out.append(str(colors[cur]));cur=links[cur]-1
        candidates.append(''.join(out))
    assert sorted(candidates)[k-1]==clue
    for reply in [clue,clue+'\n',clue+'\r\n',clue+'\n\n']:
        assert digit_check(reply,clue);positive+=1
    wrong=('2' if clue[0]!='2' else '3')+clue[1:]
    for reply in [wrong,clue+' ',clue+'\n0',' '+clue,clue[:-1]]:
        assert not digit_check(reply,clue);negative+=1
checked('final_crlf_checker_regression',positive=positive,negative=negative,scope='Extracted check only; live Stepik not exercised')

# Independent references for changed input domains and stored test cases.
for dataset,clue in b(3383209)['source']['test_cases']:
    n=int(dataset);assert 0<=n<=10**9
    assert int(clue)==n*(n-1)//2+1
    assert n*(n-1)<=2**63-1
checked('extension_cord_test_domain',test_cases=len(b(3383209)['source']['test_cases']),maximum_n=10**9)

odd_count=0
for dataset,clue in b(3384518)['source']['test_cases']:
    t=list(map(int,dataset.split()));assert t[0]==len(t)-1 and 1<=t[0]<=1000
    out=[]
    for n in t[1:]:
        assert 1<=n<=2**31-1;value=0
        while n:value+=((n+1)//2)**2;n//=2
        assert value<2**63;out.append(value);odd_count+=1
    assert out==list(map(int,clue.split()))
checked('largest_odd_divisor_sum',individual_inputs=odd_count)

def constrained(length,modulus,constraints):
    assigned_positions={}
    for kind,word in constraints:
        if len(word)>length:return 0
        start=0 if kind=='prefix' else length-len(word)
        for i,ch in enumerate(word,start):
            if i in assigned_positions and assigned_positions[i]!=ch:return 0
            assigned_positions[i]=ch
    return pow(26,length-len(assigned_positions),modulus)
def reference_string_count(length,modulus,a,z):
    left=[('prefix',a),('suffix',z)];right=[('prefix',z),('suffix',a)]
    return (constrained(length,modulus,left)+constrained(length,modulus,right)-constrained(length,modulus,left+right))%modulus
string_cases=0
for dataset,clue in b(3446002)['source']['test_cases']:
    lines=dataset.splitlines();count=int(lines[0]);assert len(lines)==1+3*count and 1<=count<=100
    out=[]
    for i in range(count):
        length,modulus=map(int,lines[1+3*i].split());a,z=lines[2+3*i:4+3*i]
        assert 1<=length<=10**9 and 1<=modulus<=10000
        assert 1<=len(a)<=200 and 1<=len(z)<=200
        assert all(ch in string.ascii_lowercase for ch in a+z)
        out.append(reference_string_count(length,modulus,a,z));string_cases+=1
    assert out==list(map(int,clue.split()))
for length,a,z in [(1,'a','a'),(1,'a','b'),(2,'a','b'),(2,'a','aa'),(2,'ab','b'),(2,'ab','ab'),(2,'ab','ba')]:
    words=(''.join(v) for v in itertools.product(string.ascii_lowercase,repeat=length))
    brute=sum((w.startswith(a) and w.endswith(z)) or (w.startswith(z) and w.endswith(a)) for w in words)
    assert reference_string_count(length,10000,a,z)==brute
checked('prefix_suffix_test_domain_and_reference',individual_inputs=string_cases,small_exhaustive_cases=7)

for dataset,clue in b(3446094)['source']['test_cases']:
    s=dataset.strip();assert 1<=len(s)<=10**5 and all(c in string.ascii_lowercase for c in s)
    expected=-1 if len(set(s))==1 else len(s)-(s==s[::-1])
    assert int(clue)==expected
checked('non_palindrome_test_alphabet',test_cases=len(b(3446094)['source']['test_cases']))

# Bounded compilation/execution of manually reviewed safe fragments.
common='#include <cassert>\n#include <iostream>\n#include <string>\n#include <cstring>\n#include <type_traits>\n#include <climits>\n'
def wrapped(body,tail=''):return common+'\nint main() {\n'+body+'\n'+tail+'\n}\n'
with tempfile.TemporaryDirectory(prefix='core-fixed-checks-') as tmp:
    TMP=Path(tmp)
    def compile_run(name,source,standard='c++20',inputs=('',),expected=None,c=False,run=True):
        ext='.c' if c else '.cpp';path=EXAMPLES/(name+ext);path.write_text(source)
        binary=TMP/name;compiler=args.c_compiler if c else args.compiler
        command=[compiler,f'-std={standard}','-Wall','-Wextra','-pedantic-errors',str(path),'-o',str(binary)]
        cr=subprocess.run(command,text=True,capture_output=True,timeout=20)
        row={'name':name,'standard':standard,'source':path.name,'compile_returncode':cr.returncode,'diagnostic':cr.stderr.replace(str(EXAMPLES),'core-validation')[:1800],'runs':[]}
        report['compilations'].append(row)
        assert cr.returncode==0,(name,cr.stderr)
        if run:
            for i,stdin in enumerate(inputs):
                rr=subprocess.run([str(binary)],input=stdin,text=True,capture_output=True,cwd=TMP,timeout=3)
                row['runs'].append({'input':stdin[:150],'returncode':rr.returncode,'stdout':rr.stdout[:2000],'stderr':rr.stderr[:1000]})
                expected_rc=0
                if isinstance(expected,list) and isinstance(expected[i],dict):expected_rc=expected[i].get('returncode',0)
                assert rr.returncode==expected_rc,(name,rr.returncode,rr.stderr)
                if expected is not None:
                    target=expected[i] if isinstance(expected,list) else expected
                    if isinstance(target,dict):target=target.get('stdout_contains')
                    if target is not None:assert target in rr.stdout,(name,target,rr.stdout)
        row['passed']=True

    compile_run('array_initialization',wrapped('int a[4]{}; a[0]=42; int t=a[3];\nint mat[][2]={1,2,3};\nstatic_assert(std::is_array_v<decltype(a)>);\nassert(t==0 && sizeof(mat)/sizeof(int)==4 && mat[1][1]==0);'))
    compile_run('pointer_indirection',wrapped(snippet(3212969,'int** pptr'),'assert(var==30);'))
    compile_run('char_pointer_output',snippet(3212970,'const char text[]'),expected='character=N\nstring=N')
    compile_run('pointer_increment',snippet(3212990,'int main()'),expected='10\n20\n10')
    compile_run('pointer_offsets',wrapped(snippet(3212990,'double values[]'),'assert(pd==values+1 && pc==letters);'),expected='30.6A')
    compile_run('pointer_difference',wrapped(snippet(3212990,'auto distance'),'assert(distance==2);'),expected='2')
    compile_run('pointer_precedence',wrapped(snippet(3212990,'int b = *p++;'),'assert(b==30 && values[1]==21 && p==values+2);'))
    compile_run('array_complete_loop',wrapped(snippet(3213003,'ptr != a + 5')),expected='value=5')
    compile_run('matrix_nested_iteration',snippet(3213003,'int a[3][4]'),expected='9\t10\t11\t12')
    compile_run('valid_commuted_subscript',wrapped('int arr[]{1,2,3,4,5,6};int a=2[arr]-arr[3]+arr[4];assert(a==4);'))
    compile_run('string_array_new',wrapped('char* p=new char[]{"Hello"};assert(std::strcmp(p,"Hello")==0);delete[] p;'),standard='c++11')
    compile_run('matrix_delete_arrays',wrapped('\n'.join(snippets(3333775))))
    compile_run('malloc_basic_c',snippet(3213208,'int* p = malloc(100);'),standard='c17',c=True)
    compile_run('malloc_scanf_c',snippet(3213208,'const unsigned maxNumber'),standard='c17',c=True,inputs=('0\n','5\n','100\n','bad\n'),expected=[{'returncode':0},{'stdout_contains':'0 1 4 9 16'},{'stdout_contains':'9801'},{'returncode':1}])
    compile_run('realloc_words_c',snippet(3213210,'char** words = malloc'),standard='c17',c=True,inputs=('hello world end\n','a b c d e f g h i j k l end\n'),expected=['hello\nworld\n','k\nl\n'])
    compile_run('realloc_aliases_c',snippet(3213210,'int* replacement = realloc'),standard='c17',c=True,expected='0 1 2 3 4 5 6 7 8 9')
    compile_run('noexcept_copy',snippet(3214910,'T copy_object')+'\n#include <cassert>\nstruct MayThrow { MayThrow(const MayThrow&) noexcept(false) {} };\nint main(){int n=42;static_assert(noexcept(copy_object(n)));static_assert(!std::is_nothrow_copy_constructible<MayThrow>::value);assert(copy_object(n)==42);}\n')
    compile_run('string_compare_and_accessor',common+'int main(){std::string s="default";assert(!(s!="default"));s="x";assert(s!="default");static_assert(std::is_same_v<decltype(s.c_str()),const char*>);assert(std::strcmp("a","b")<0);assert(std::strcmp("a","a")==0);assert(std::strcmp("b","a")>0);static_assert(std::is_same_v<decltype(\'a\'),char>);}\n')
    compile_run('setw_matrix',snippet(3215024,'int **array_generator'),expected='35')
    compile_run('char_promotion',wrapped(snippet(3252940,'signed char a = 105'),'static_assert(CHAR_BIT==8);static_assert(std::is_same_v<decltype(a+b),int>);assert(sum==135 && narrowed==-121);'))
    compile_run('sum_digits',common+snippet(3253129,'int SumOfDigits')+'\nint main(){assert(SumOfDigits(0)==0);assert(SumOfDigits(1)==1);assert(SumOfDigits(10)==1);assert(SumOfDigits(100)==1);assert(SumOfDigits(999)==27);assert(CountInterestingInInterval(1000)==100);}\n')
    tests=snippet(3253503,'TEST(InterestingNumbers, test_ordinary_1)');tests=tests.replace('#include "pch.h"','')
    names=re.findall(r'TEST\(InterestingNumbers,\s*(\w+)\)',tests);assert len(names)==7
    prefix='#include <cassert>\n#define TEST(suite,name) void suite##_##name()\n#define ASSERT_EQ(a,b) assert((a)==(b))\n'
    compile_run('google_test_two_arguments',prefix+tests+'\nint main(){'+''.join('InterestingNumbers_'+name+'();' for name in names)+'}\n')
    for sid in [3253503,3253553]:
        for call in re.findall(r'\bTEST\(([^)]+)\)',b(sid)['text']):
            assert len(call.split(','))==2,(sid,call)
    compile_run('string_constructors',snippet(3214903,'std::string S =')+'\n#include <cassert>\nint main(){assert(empty.empty() && copy=="abcdef" && repeated=="xxx" && one_character=="x" && part=="bc");}\n')
    compile_run('string_literal_const',snippet(3214903,'const char* ps')+'\n#include <cassert>\nint main(){assert(s3=="Hello" && s6=="A");}\n')
    compile_run('quadratic_example',snippet(3213242,'int main()'),expected='1\n2\n3\n4\n5\n6\n7\n8\n9')
    compile_run('binary_search_with_sort',snippet(3213247,'int main()'),inputs=('9 8 7 6 5 4 3 2 1 0\n3\n',),expected='равен: 3')
    compile_run('binary_search_bounds',common+snippet(3215192,'int SearchingAlgorithm')+'\nint main(){int a[]{1,2,3,4,5,6,7,8,9,10};assert(SearchingAlgorithm(a,0,9,2)==1);assert(SearchingAlgorithm(a,0,9,1)==0);assert(SearchingAlgorithm(a,0,9,10)==9);assert(SearchingAlgorithm(a,0,9,11)==-1);assert(SearchingAlgorithm(nullptr,0,-1,1)==-1);}\n')

report['summary']={'checks_passed':len(report['checks']),'compilations_passed':len(report['compilations']),'runs_passed':sum(len(x['runs']) for x in report['compilations']),'assigned_findings':len(assigned),'changed_steps':len(changed)}
report['source_sha256']={str(paths[sid].relative_to(ROOT)):hashlib.sha256(paths[sid].read_bytes()).hexdigest() for sid in changed}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report['summary'],ensure_ascii=False))
