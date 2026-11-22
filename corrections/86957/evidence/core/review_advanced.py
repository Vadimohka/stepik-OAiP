#!/usr/bin/env python3
"""Independent peer review of the ten advanced-module corrections."""
from hashlib import sha256
import html
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).parent
IDS=[3215234,3215235,3215236,3212956,3215244,3570303,3669142,3669172,3759850,3759914]


def document(sid,corrected=False):
    p=next((ROOT/'courses/86957/steps').rglob(f'*_{sid}_*.step'))
    if corrected:
        q=ROOT/'corrections/86957/steps'/p.parent.name/p.name
        if q.exists():p=q
    return p,json.loads(p.read_text())


def blocks(sid,corrected=False):
    _,d=document(sid,corrected)
    return [html.unescape(re.sub('<[^>]+>','',t)) for t in re.findall('<pre[^>]*>(.*?)</pre>',d['block']['text'],re.S)]


def rbt(corrected):
    return blocks(3570303,corrected)[1]+'\n'+'\n'.join(blocks(3570304))+'\n'+'\n'.join(blocks(3570333))


def compile_run(name,source,standard,compile_success=True,run_code=0):
    path=OUT/(name+'.cpp');path.write_text(source)
    with tempfile.TemporaryDirectory(dir=OUT,prefix='peer_') as temp:
        exe=Path(temp)/'program'
        result=subprocess.run(['g++','-std='+standard,'-Wall','-Wextra','-pedantic-errors',str(path),'-o',str(exe)],text=True,capture_output=True)
        assert (result.returncode==0)==compile_success,(name,result.stderr)
        row={'name':name,'standard':standard,'expected_compile_success':compile_success,
             'compile_returncode':result.returncode,'diagnostics':result.stderr}
        if compile_success:
            run=subprocess.run([str(exe.resolve())],text=True,capture_output=True)
            assert run.returncode==run_code,(name,run.returncode,run.stderr)
            row.update(expected_run_returncode=run_code,run_returncode=run.returncode)
        return row


def main():
    notes={
      3215234:'All string pointers are initialized before any failure path; each malloc/scanf failure either owns nothing or calls the common cleanup. size=0 still permits malloc(0) returning NULL. Valid input behavior is preserved.',
      3215235:'Both string pointers receive malloc results before the joint test; freeModel may safely free either NULL and releases the surviving allocation. The helper no longer calls strcpy on NULL.',
      3215236:'Same allocation-failure correction as the previous independent example; it preserves pointers to make and id and runs them only after successful allocation.',
      3212956:'The revised union explanation distinguishes permitted scalar lifetime start from assignment to an inactive std::string and notes that the old member is not automatically destroyed. It corrects a materially false general rule.',
      3215244:'Ints was first defined only in the following step, whereas the preceding step defines Floats. Adding the existing intended definition makes this fragment usable at its actual position; field types match the subsequent example.',
      3570303:'A copy of the shared_ptr root shares mutable nodes while keeping two separate root handles. Rotations through the copied owner can make original keys unreachable. Deleting copy construction/assignment is a minimal ownership policy; implicit move is unavailable too. No current course usage requires copying this tree.',
      3669142:'The example is intentionally invalid because Display is incomplete at the friend member declaration. The old missing class boundary introduced a second unrelated syntax error; the patch restores Display while preserving the intended failure.',
      3669172:'Default card construction now initializes both fields. Invalid or failed position input exits before selected-card comparison. Valid positions 1--3 retain behavior. Added clocale supplies the declared setlocale dependency.',
      3759850:'Unbounded strcpy into char[20]/char[40] had no documented length precondition. std::string preserves complete names; every affected printf %s receives c_str(). The virtual price base and price calculation are unchanged.',
      3759914:'An abstract base may contain virtual implementations inherited by a concrete derived class. The prior assertion that only nonvirtual elements are inherited was false. The replacement preserves the abstract-instantiation restriction.'
    }
    rows=[]
    for sid in IDS:
        p,old=document(sid);q,new=document(sid,True)
        a=json.loads(json.dumps(old));b=json.loads(json.dumps(new))
        a['block'].pop('text');b['block'].pop('text')
        assert a==b,(sid,'unrelated fields changed')
        rows.append({'step_id':sid,'status':'approved','changed_fields':['block.text'],
                     'corrected_path':str(q.relative_to(ROOT)),
                     'reviewed_sha256':sha256(q.read_bytes()).hexdigest(),'assessment':notes[sid]})
    repro='''
int main() {
    RBT<int,int> original, other;
    original.add(20,200); original.add(10,100);
    other = original;
    other.add(0,0); // right rotation of the shared original root
    return original.contains(10) ? 0 : 42;
}
'''
    ownership='''
#include <type_traits>
#include <map>
static_assert(!std::is_copy_constructible_v<RBT<int,int>>);
static_assert(!std::is_copy_assignable_v<RBT<int,int>>);
static_assert(!std::is_move_constructible_v<RBT<int,int>>);
static_assert(!std::is_move_assignable_v<RBT<int,int>>);
int main() {
    RBT<int,int> tree;
    for(int i=20;i>=0;--i) tree.add(i,10*i);
    for(int i=0;i<=20;++i) if(tree.findValueWithKey(i)!=10*i) return 1;
    for(int i=0;i<=20;i+=2) tree.remove(i);
    for(int i=0;i<=20;++i) if(tree.contains(i)!=(i%2!=0)) return 2;
    tree.clear();
    for(int i=0;i<=20;++i) if(tree.contains(i)) return 3;
}
'''
    names=blocks(3759850,True)[4]
    # Retain the class definitions exactly and replace only the demonstration main.
    names=names[:names.index('int main()')]+'''
int main() {
    for (int n : {0,19,20,39,40,200}) {
        const std::string first(n,'a'), second(n+1,'b'), total(2*n,'c');
        unit_box item(first.c_str(),4,second.c_str(),6,total.c_str(),'p');
        if(item.unit::name!=first || item.box::name!=second || item.name!=total) return 1;
        price* from_unit=static_cast<unit*>(&item);
        price* from_box=static_cast<box*>(&item);
        if(from_unit!=from_box || from_unit->val!=10 || from_unit->type!='p') return 2;
        auto copy=item;
        copy.name += "changed";
        if(item.name!=total) return 3;
        item.print();
    }
}
'''
    executed=[]
    for standard in ('c++17','c++20'):
        executed.append(compile_run('peer_rbt_assignment_before',rbt(False)+repro,standard,True,42))
        executed.append(compile_run('peer_rbt_assignment_after',rbt(True)+repro,standard,False))
        executed.append(compile_run('peer_rbt_ownership_after',rbt(True)+ownership,standard))
        executed.append(compile_run('peer_inheritance_names_after',names,standard))
    report={'reviewer':'core_errors','status':'approved','steps_reviewed':10,'findings':rows,
            'independent_executions':executed,
            'independent_evidence':['Copy-assignment counterexample causes original key 10 to disappear after a rotation in the assigned tree; corrected copy assignment is rejected at compile time.',
                                    'The corrected tree retains insertion, lookup, deletion and clear behavior for 21 keys; noncopyable/nonmovable traits hold.',
                                    'All three name fields preserve strings at lengths 0,19,20,39,40,200 (and corresponding combined lengths); the price base stays shared and copy of strings stays independent.'],
            'limitations':['Read all ten diffs and associated advanced validation harnesses; independently executed the two highest-risk changed code examples under GCC C++17/C++20.',
                           'Did not rerun the entire advanced sanitizer suite or Windows/MSVC.']}
    (OUT/'peer_advanced.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Approved 10 advanced corrections; 8 independent GCC C++17/C++20 compilation checks.')


if __name__=='__main__':main()
