#!/usr/bin/env python3
"""Targeted, local checks of second-round module 10 explanations/examples."""
import hashlib
import html
import itertools
import json
import pathlib
import re
import subprocess
import tempfile
from decimal import Decimal,localcontext
from fractions import Fraction

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[4]
PATHS={int(p.name.split('_')[1]):p for lid in [770594,770595,771129] for p in (ROOT/f'courses/86957/steps/{lid}').glob('*.step')}
STEPS={sid:json.loads(path.read_text()) for sid,path in PATHS.items()}
checks=[]
def record(name,**values):checks.append(dict(check=name,passed=True,**values))
def code(sid):
    raw=re.findall(r'<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>',STEPS[sid]['block']['text'],re.S)[0]
    return html.unescape(re.sub('<[^>]*>','',raw))

def interpolation(a,x):
    left,right=0,len(a)-1
    while left<=right and a[left]<=x<=a[right]:
        if a[left]==a[right]: return left if a[left]==x else -1
        mid=left+(x-a[left])*(right-left)//(a[right]-a[left])
        assert left<=mid<=right
        if a[mid]==x:return mid
        if a[mid]<x:left=mid+1
        else:right=mid-1
    return -1

def main():
    assert Fraction(15*99,195)//1==7
    total=0
    for size in range(7):
        for a in itertools.combinations_with_replacement(range(5),size):
            for x in range(-1,6):
                index=interpolation(a,x)
                assert (index>=0)==(x in a),(a,x,index)
                if index>=0:assert a[index]==x
                total+=1
    for a in [list(range(100))+[10**9],[0,10**18],[7]*100]:
        for x in [-1,0,1,7,99,100,10**9,10**18]:
            index=interpolation(a,x)
            assert (index>=0)==(x in a)
            if index>=0:assert a[index]==x
            total+=1
    record('interpolation_formula_and_search_against_linear_membership',inputs=total,example_index=7)
    with localcontext() as ctx:
        ctx.prec=60
        assert Decimal(1494)**Decimal('0.63')<100<Decimal(1495)**Decimal('0.63')
    record('hidden_constant_crossover',last_before=1494,first_after=1495)
    pairs=[(n,p) for n in range(2,200) for p in range(2,min(n,30)+1)]+[(2*10**9,p) for p in [2,3,46340]]
    for n,p in pairs:
        value=n;outer=inner=0
        while value>1:
            outer+=1;inner+=max(0,value%p-1);value//=p
        power=p;ceiling=1
        while power<n:power*=p;ceiling+=1
        assert outer<=ceiling and inner<=outer*(p-2)
        assert (p-1)**2<=2147483647
    record('factmod_loop_bound_and_int_product_bound',parameter_pairs=len(pairs))
    build_dir=HERE/'checks';build_dir.mkdir(exist_ok=True)
    programs={
        'size_3213241':code(3213241),
        'heap_example_3215179':code(3215179),
        'heap_harness':code(3215179).split('int main()')[0]+'''\n#include <algorithm>
#include <cassert>
#include <vector>
int main() {
    std::vector<std::vector<int>> tests{{},{1},{1,1,1},{3,2,1},{-7,2,0,2,-7},{1,2,3,4,5}};
    for (auto a : tests) {
        auto expected = a;
        std::sort(expected.begin(), expected.end());
        heapSort(a.data(), static_cast<int>(a.size()));
        assert(a == expected);
    }
}
''',
        'factmod_harness':code(3408628)+'''\n#include <cassert>
#include <limits>
int main() {
    static_assert(std::numeric_limits<int>::max() == 2147483647);
    for (int p : {2, 3, 46340}) {
        int answer = factmod(2000000000, p);
        assert(0 <= answer && answer < p);
    }
}
''',
    }
    # initializer_list is deliberately explicit in the harness as well.
    programs['factmod_harness']='#include <initializer_list>\n'+programs['factmod_harness']
    builds=[]
    with tempfile.TemporaryDirectory(prefix='module10-',dir=HERE) as tmp:
        for name,source in programs.items():
            path=build_dir/(name+'.cpp');path.write_text(source)
            for standard in ['c++17','c++20']:
                binary=pathlib.Path(tmp)/(name+'-'+standard)
                subprocess.run(['g++','-std='+standard,'-Wall','-Wextra','-pedantic-errors','-fsanitize=undefined','-fno-sanitize-recover=undefined',str(path),'-o',str(binary)],check=True,capture_output=True,text=True,timeout=30)
                run=subprocess.run([str(binary)],capture_output=True,text=True,check=True,timeout=3)
                assert not run.stderr,run.stderr
                if name.startswith('size_'):assert run.stdout=='5'
                if name.startswith('heap_example_'):assert run.stdout.split()[-5:]==['0','3','8','19','48']
                builds.append(dict(source=str(path.relative_to(ROOT)),standard=standard,run_passed=True))
    record('cpp_examples_and_harnesses',builds=len(builds),runs=len(builds),sanitizer='undefined',details=builds)
    result=dict(course_id=86957,module=10,all_passed=True,checks=checks,
                step_file_sha256={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for sid,path in PATHS.items() if STEPS[sid]['block']['name']!='code'})
    (HERE/'module10_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(all_passed=True,checks=len(checks),builds=len(builds),interpolation_inputs=total)))

if __name__=='__main__':main()
