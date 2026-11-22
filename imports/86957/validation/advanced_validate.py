"""Targeted validation of edited course steps, without running deliberate UB examples."""
from advanced_validation_common import ROOT, WORK, PATHS, block, codes
from concurrent.futures import ThreadPoolExecutor
import collections
import html
import hashlib
import json
import os
import re
import subprocess
import sys

OUT = WORK / 'advanced_checks'
OUT.mkdir(exist_ok=True)
results = []
jobs = []

def check(name, condition, detail=''):
    results.append({'name': name, 'status': 'passed' if condition else 'failed', 'detail': detail})

audit = json.loads((ROOT / 'audit/findings.json').read_text(encoding='utf-8'))
findings = audit['findings']
bundle_path = ROOT / 'courses/86957/course.json'
bundle_bytes = bundle_path.read_bytes()
bundle = json.loads(bundle_bytes)
baseline_steps = {int(step['id']): step for step in bundle['step_sources']}
baseline_export_time = '2026-11-22T18:35:40Z'
baseline_info = {
    'source_bundle': 'courses/86957/course.json',
    'source_bundle_sha256': hashlib.sha256(bundle_bytes).hexdigest(),
    'baseline_export_time': baseline_export_time,
    'audit_source_commit': audit.get('source_commit'),
}
expected = {f['id'] for f in findings if 11 <= f['module'] <= 20}
logpath = WORK / 'advanced_changes.json'
changes = json.loads(logpath.read_text())
covered = {x['finding_id'] for x in changes}
check('finding_coverage', expected <= covered and len(expected) == 61,
      f'{len(expected & covered)}/61; extra={sorted(covered-expected)}')
ids = sorted({sid for x in changes for sid in x['changed_step_ids']})
for sid in ids:
    path = PATHS[sid]
    baseline = baseline_steps[sid]
    current = json.loads(path.read_text())
    check(f'metadata_{sid}', current['id'] == str(baseline['id']) and current['time'] == baseline_export_time and
          set(current) == {'block','id','time'} and current['block']['name'] == baseline['block']['name'])
    check(f'changed_{sid}', current['block'] != baseline['block'])
    if current['block']['name'] == 'choice':
        b=current['block'];s=b['source'];opts=s['options']; correct=sum(o['is_correct'] for o in opts)
        check(f'choice_shape_{sid}', s['sample_size'] <= len(opts) and correct > 0 and
              (s['is_multiple_choice'] or correct==1) and s['is_multiple_choice']==b['options']['is_multiple_choice'])

check('size_answers_3426003', [x['options'][0]['text'] for x in block(3426003)['source']['components'] if x['type']=='input'] == ['8','8','22','22'])
check('operator_index_key', [html.unescape(o['text']) for o in block(4718139)['source']['options'] if o['is_correct']] == ['T&'])
check('weak_question_key', [o['text'] for o in block(4718330)['source']['options'] if o['is_correct']] == ['q пуст, а w.expired() возвращает true.'])
check('control_U0002_removed', all('\u0002' not in block(sid)['text'] for sid in [4035439,4035460]))
check('wrong_images_replaced', all('<img' not in block(sid)['text'] and '<table>' in block(sid)['text'] for sid in [4035427,4035430,4035439]))
old=baseline_steps[5850209]['block']['source']['test_cases']
new=block(5850209)['source']['test_cases']
check('yaml_cases_only_lowercase_key_changed', json.dumps(new,ensure_ascii=False)==json.dumps(old,ensure_ascii=False).replace('IiTP','iitp'))
check('yaml_no_uppercase_iitp', 'IiTP' not in json.dumps(block(5850209),ensure_ascii=False))

if '--structural-only' in sys.argv[1:]:
    failed = [item for item in results if item['status'] != 'passed']
    report = dict(baseline_info, mode='structural_only', finding_count=len(expected),
                  changed_step_count=len(ids), compiled_case_count=0,
                  passed=len(results)-len(failed), failed=len(failed), results=results,
                  limits=['Only baseline loading, metadata, edited blocks, choice keys and data synchronization were checked. No C++ compiler or executable was launched.'])
    (WORK / 'advanced_structural_validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('mode','passed','failed','compiled_case_count','changed_step_count')},ensure_ascii=False))
    for item in failed:
        print('FAILURE', json.dumps(item, ensure_ascii=False))
    raise SystemExit(bool(failed))

def add(name, code, run=False, stdin='', expected_output=None, standards=('c++17',), sanitize=False):
    for std in standards:
        suffix=std.replace('+','p')
        case=name+'_'+suffix+('_san' if sanitize else '')
        source=OUT/(case+'.cpp');source.write_text(code+'\n')
        jobs.append({'name':case,'source':str(source),'run':run,'stdin':stdin,'expected_output':expected_output,
                     'standard':std,'sanitize':sanitize})

for sid,index,input_data in [
    (3215199,1,''),(3215231,0,''),(3215232,0,''),(3215233,0,''),
    (3215234,0,'2\nalice\none\nbob\ntwo\n'),(3215235,0,''),(3215235,1,''),(3215236,0,''),
    (3216509,3,''),(3668927,0,''),(3669140,1,'1\n2\n'),(3669140,2,''),
    (3760025,0,''),(3759850,1,''),(3759850,4,''),(3759851,2,''),(3759914,0,''),
    (3569919,1,''),(4040986,0,''),(4040986,1,''),(3569327,0,''),
    (4047616,4,''),(4047627,1,''),(4047627,2,'')
]:
    add(f'lesson_{sid}_{index}',codes(sid)[index],True,input_data)
for i,c in enumerate(codes(3760047)):
    if 'int main()' in c:add(f'lesson_3760047_{i}',c,True)
add('lesson_3668999_distance',codes(3668999)[0]+'\n'+codes(3668999)[2],True,'1\n2\n')
add('lesson_3668952_enum',codes(3668952)[0]+'\nint main() {}')
add('lesson_4036909_skeleton',codes(4036909)[0]+'\nint main() {}')

add('file_counter',codes(3215203)[3]+r'''
#include <cassert>
int main() {
    std::FILE* f=std::fopen("counter.bin","w+b"); assert(f);
    int value=5; assert(std::fwrite(&value,sizeof value,1,f)==1);
    assert(increment_counter(f,0));
    assert(std::fseek(f,0,SEEK_SET)==0); assert(std::fread(&value,sizeof value,1,f)==1); assert(value==6);
    value=std::numeric_limits<int>::max();
    assert(std::fseek(f,0,SEEK_SET)==0); assert(std::fwrite(&value,sizeof value,1,f)==1);
    assert(!increment_counter(f,0)); assert(!increment_counter(nullptr,0));
    std::fclose(f);
}''',True,standards=('c++17','c++20'))

add('abi_sizes',codes(3426003)[0]+'\n'+codes(3426003)[1]+r'''
struct inner_reordered { int y; bool x; char z; };
#pragma pack(push,2)
struct T_reordered { double k; int i; inner_reordered in; short j; };
#pragma pack(pop)
struct alignas(16) ArrayOfChars { char A[10]; char B[8]; };
static_assert(sizeof(bool)==1 && sizeof(char)==1 && sizeof(int)==4 && alignof(int)==4);
static_assert(sizeof(short)==2 && sizeof(double)==8 && alignof(double)==8);
static_assert(sizeof(inner)==8 && sizeof(inner_reordered)==8);
static_assert(sizeof(T)==22 && sizeof(T_reordered)==22);
static_assert(sizeof(ArrayOfChars)==32);
union Padded { int x; char bytes[5]; };
static_assert(sizeof(Padded)>5);
int main() {}''',True,standards=('c++17','c++20'))

add('value_categories_and_distractors',r'''
#include <cassert>
#include <memory>
#include <string>
#include <type_traits>
#include <utility>
#include <map>
struct Array { using T=int; T a[1]{}; T& operator[](int i) { return a[i]; } };
struct MoveOnly { std::unique_ptr<int> value; };
int main() {
    int x=1; const int n=2;
    static_assert(std::is_same_v<decltype((x)),int&>);
    static_assert(std::is_same_v<decltype((n)),const int&>);
    static_assert(std::is_same_v<decltype(std::move(x)),int&&>);
    static_assert(std::is_lvalue_reference_v<decltype(("abc"))>);
    const int& temporary=2; assert(temporary==2);
    std::string{}="abc";
    Array a; a[0]=42; assert(a.a[0]==42);
    static_assert(std::is_assignable_v<int&,int>);
    static_assert(!std::is_assignable_v<const int&,int>);
    static_assert(!std::is_assignable_v<int,int>);
    static_assert(!std::is_assignable_v<int*&,int>);
    MoveOnly original{std::make_unique<int>(7)};
    MoveOnly moved=std::move(original); assert(!original.value && *moved.value==7);
    static_assert(!std::is_convertible_v<std::unique_ptr<int>,bool>);
    auto p=std::make_shared<int>(42); std::weak_ptr<int> w=p; p.reset(); auto q=w.lock();
    assert(!q && w.expired() && w.use_count()==0);
    std::map<int,int> map{{1,7},{2,7}}; assert(map.size()==2);
    std::multimap<int,int> mm{{1,7},{1,8}}; assert(mm.count(1)==2);
}''',True,standards=('c++17','c++20'))

add('teaching_unique',codes(3570166)[0]+r'''
#include <cassert>
#include <type_traits>
#include <utility>
int main() {
    static_assert(!std::is_convertible_v<unique_ptr<int>,bool>);
    unique_ptr<int> a(new int(7)); assert(a && *a==7);
    unique_ptr<int> b(std::move(a)); assert(a.isNull() && *b==7);
    b=std::move(b); assert(*b==7);
    unique_ptr<int> c; c=std::move(b); assert(b.isNull() && *c==7);
}''',True)

add('teaching_shared_demo',codes(3570213)[0]+'\n'+codes(3570213)[1],True,
    expected_output='2\ntrue\nfalse\n')
shared_tests=codes(3570213)[0]+r'''
#include <cassert>
#include <iostream>
struct Tracked {
    static int destroyed;
    teaching::weak_ptr<Tracked> self;
    ~Tracked() {
        assert(self.expired());
        assert(!self.lock());
        self.reset(); // последний явный weak_ptr может исчезнуть внутри деструктора T
        ++destroyed;
    }
};
int Tracked::destroyed=0;
struct MemberWeak {
    static int destroyed;
    teaching::weak_ptr<MemberWeak> self;
    ~MemberWeak() { assert(self.expired()); ++destroyed; }
};
int MemberWeak::destroyed=0;
int main() {
    { teaching::shared_ptr<Tracked> p(new Tracked); p->self=p; p.reset(); }
    assert(Tracked::destroyed==1);
    { teaching::shared_ptr<MemberWeak> p(new MemberWeak); p->self=p; }
    assert(MemberWeak::destroyed==1);
    teaching::weak_ptr<Tracked> external;
    {
        teaching::shared_ptr<Tracked> p(new Tracked); p->self=p; external=p;
        auto copy=p; assert(p.use_count()==2);
        auto locked=external.lock(); assert(p.use_count()==3);
        teaching::shared_ptr<Tracked> moved(std::move(copy)); assert(!copy && p.use_count()==3);
        p=p; assert(p.use_count()==3); p=std::move(p); assert(p.use_count()==3);
        auto weakcopy=external; auto weakmove=std::move(weakcopy); assert(weakcopy.expired());
        weakmove=weakmove; weakmove=std::move(weakmove); assert(!weakmove.expired());
    }
    assert(Tracked::destroyed==2 && external.expired() && !external.lock());
    auto expired_copy=external; external.reset(); assert(expired_copy.expired()); expired_copy.reset();
    teaching::weak_ptr<int> empty; assert(empty.expired() && !empty.lock());
    std::cout << "shared lifetime and self-weak checks passed\n";
}'''
add('teaching_shared_regression',shared_tests,True,standards=('c++17','c++20'))
add('teaching_shared_regression',shared_tests,True,sanitize=True)

add('casts_and_queue',r'''
#include <cassert>
#include <deque>
#include <queue>
#include <typeinfo>
struct B { virtual ~B()=default; }; struct D:B {};
struct Nonpoly {}; struct Child:Nonpoly {};
int main() {
    std::deque<int> values(3); std::queue<int> q(values);
    assert(q.size()==3 && q.front()==0 && q.back()==0 && !q.empty());
    q.pop(); assert(q.size()==2);
    D d; B& b=d; assert(&static_cast<D&>(b)==&d); assert(dynamic_cast<D*>(&b)==&d);
    B other; assert(dynamic_cast<D*>(&other)==nullptr);
    bool threw=false; try { (void)dynamic_cast<D&>(other); } catch(const std::bad_cast&) { threw=true; }
    assert(threw);
    Child child; assert(dynamic_cast<Nonpoly*>(&child)==static_cast<Nonpoly*>(&child));
    assert(static_cast<unsigned long long>(3.14159)==3);
}''',True,standards=('c++17','c++20'))

avl=codes(3570281)[0]+r'''
#include <cassert>
#include <map>
#include <random>
#include <climits>
int validate(const std::shared_ptr<Node>& node, long long lo, long long hi, std::map<int,std::string>& got) {
    if (!node) return 0;
    assert(node->key>lo && node->key<hi);
    int l=validate(node->left,lo,node->key,got), r=validate(node->right,node->key,hi,got);
    assert(l-r<=1 && r-l<=1); assert(node->height==1+std::max(l,r));
    got.emplace(node->key,node->value); return node->height;
}
void checkTree(const std::shared_ptr<Node>& root,const std::map<int,std::string>& expected) {
    std::map<int,std::string> actual; validate(root,LLONG_MIN,LLONG_MAX,actual); assert(actual==expected);
}
int main() {
    std::shared_ptr<Node> root; std::map<int,std::string> expected;
    for (auto [key,value]:std::map<int,std::string>{{1,"one"},{2,"two"},{3,"three"}}) {
        root=insert(root,key,value);expected.emplace(key,value);checkTree(root,expected);
    }
    root=deleteNode(root,2);expected.erase(2);checkTree(root,expected);
    assert(root->key==3 && root->value=="three");
    std::mt19937 random(42);
    for (int i=0;i<500;++i) {
        int key=static_cast<int>(random()%50);
        if (random()%2) { auto value=std::to_string(i); root=insert(root,key,value);expected.emplace(key,value); }
        else {root=deleteNode(root,key);expected.erase(key);}
        checkTree(root,expected);
    }
    for (int key=0;key<50;++key) {root=deleteNode(root,key);expected.erase(key);checkTree(root,expected);}
    assert(!root);
}'''
add('avl_key_value_and_balance',avl,True,standards=('c++17','c++20'))

rbt=codes(3570303)[1]+'\n'+'\n'.join(codes(3570304))+'\n'+'\n'.join(codes(3570333))+r'''
#include <cassert>
#include <climits>
#include <map>
#include <random>
#include <string>
class CheckedTree : public RBT<int,std::string> {
    int visit(shared_ptr<Node> node,Node* parent,long long lo,long long hi,std::map<int,std::string>& got) {
        if (!node) return 1;
        assert(node->parent.lock().get()==parent);
        assert(node->key>lo && node->key<hi);
        if (!node->color) {assert(!node->left || node->left->color);assert(!node->right || node->right->color);}
        int l=visit(node->left,node.get(),lo,node->key,got);
        int r=visit(node->right,node.get(),node->key,hi,got);assert(l==r);
        got.emplace(node->key,node->data);return l+(node->color?1:0);
    }
public:
    void check(const std::map<int,std::string>& expected) {
        assert(!root || root->color);
        std::map<int,std::string> actual;visit(root,nullptr,LLONG_MIN,LLONG_MAX,actual);assert(actual==expected);
    }
};
int main() {
    CheckedTree tree;std::map<int,std::string> expected;
    for (int key:{10,5,15,2,7,12,18,1,3,6,8,11,13,17,19}) {
        auto value=std::to_string(key);tree.add(key,value);expected.emplace(key,value);tree.check(expected);
    }
    tree.remove(10);expected.erase(10);tree.check(expected);
    std::mt19937 random(21);
    for (int i=0;i<500;++i) {
        int key=static_cast<int>(random()%50);
        if (random()%2) {auto value=std::to_string(i);tree.add(key,value);expected.emplace(key,value);}
        else {tree.remove(key);expected.erase(key);}
        tree.check(expected);
    }
    for (int key=0;key<50;++key) {tree.remove(key);expected.erase(key);tree.check(expected);}
}'''
add('red_black_invariants',rbt,True,standards=('c++17','c++20'))

hash_code='#include <memory>\n#include <string>\n#include <cassert>\n'+codes(4035443)[0]+'\n'+codes(4035443)[1]+'\n'+codes(4035443)[2].replace('class HashTable {','class HashTable {\n    friend struct HashProbe;')
hash_code+=r'''
Password::Password(int i,std::string d,std::string p):ID(i),description(d),password(p){}
int Password::GetID(){return ID;}
std::string Password::GetDescription(){return description;}
std::string Password::GetPassword(){return password;}
void Password::SetDescription(std::string v){description=v;}
void Password::SetPassword(std::string v){password=v;}
PasswordList::PasswordList():count(0){}
std::shared_ptr<Password> PasswordList::GetHead(){return head;}
int PasswordList::GetCount(){return count;}
void PasswordList::AddElement(std::shared_ptr<Password> p) {
    if(tail)tail->nextElement=p;else head=p;tail=p;++count;
}
std::shared_ptr<Password> PasswordList::SearchElementByID(int id) {
    for(auto p=head;p;p=p->nextElement)if(p->GetID()==id)return p;return {};
}
HashTable::~HashTable(){for(int i=0;i<tableSize;++i)delete items[i];delete[] items;}
struct HashProbe {
    static int used(const HashTable& t){return t.tableCount;}
    static int count(const HashTable& t){int n=0;for(int i=0;i<t.tableSize;++i)n+=t.items[i]->GetCount();return n;}
    static auto get(const HashTable& t,int id){return t.items[id%t.tableSize]->SearchElementByID(id);}
};
'''
hash_code+='\n'.join(codes(4035481))+r'''
int main(){
    HashTable t(1);t.InsertElement(1,"first","a");t.InsertElement(2,"second","b");t.InsertElement(1,"updated","c");
    assert(HashProbe::used(t)==1 && HashProbe::count(t)==2);
    assert(HashProbe::get(t,1)->GetDescription()=="updated" && HashProbe::get(t,1)->GetPassword()=="c");
    assert(HashProbe::get(t,2)->GetDescription()=="second");
    HashTable u(3);for(int i=0;i<20;++i)u.InsertElement(i,"v","p");
    for(int i=0;i<20;++i)u.InsertElement(i,"new","newp");
    assert(HashProbe::used(u)==3 && HashProbe::count(u)==20);
    for(int i=0;i<20;++i)assert(HashProbe::get(u,i)->GetPassword()=="newp");
}'''
add('hash_full_buckets',hash_code,True,standards=('c++17','c++20'))

def execute(job):
    name=job['name'];exe=OUT/name
    flags=['-std='+job['standard'],'-Wall','-Wextra','-Wpedantic','-Wformat=2','-pedantic-errors','-O1','-g']
    if job['sanitize']:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
    command=['g++',*flags,job['source'],'-o',str(exe)]
    item={'name':name,'source':job['source'],'standard':job['standard'],'sanitizers':job['sanitize']}
    try:
        compiled=subprocess.run(command,capture_output=True,text=True,timeout=30)
        diagnostics=compiled.stdout+compiled.stderr
        item['compile_exit']=compiled.returncode
        if compiled.returncode:
            item.update(status='failed',stage='compile',detail=diagnostics[-5000:])
        elif job['run']:
            run_dir=OUT/(name+'_data');run_dir.mkdir(exist_ok=True)
            env=dict(os.environ)
            if job['sanitize']:env['ASAN_OPTIONS']='detect_leaks=0:abort_on_error=1'
            run=subprocess.run([str(exe)],input=job['stdin'],cwd=run_dir,capture_output=True,text=True,timeout=8,env=env)
            diagnostics+='\nRUN STDOUT:\n'+run.stdout+'\nRUN STDERR:\n'+run.stderr
            ok=run.returncode==0 and (job['expected_output'] is None or run.stdout==job['expected_output'])
            item.update(status='passed' if ok else 'failed',stage='run',run_exit=run.returncode,stdout=run.stdout[-2000:],stderr=run.stderr[-4000:])
        else:item.update(status='passed',stage='compile')
        (OUT/(name+'.log')).write_text(diagnostics)
    except subprocess.TimeoutExpired as exc:
        item.update(status='failed',stage='timeout',detail=str(exc))
    return item

with ThreadPoolExecutor(max_workers=3) as pool:
    for item in pool.map(execute,jobs):
        results.append(item)
        print(item['status'],item['name'],item.get('stage',''))

failed=[x for x in results if x['status']!='passed']
report={**baseline_info,
        'finding_count':len(expected),'changed_step_count':len(ids),'compiled_case_count':len(jobs),
        'passed':len(results)-len(failed),'failed':len(failed),'results':results,
        'limits':['Deliberate negative/undefined-behavior examples were not executed.',
                  'Hash test supplies omitted Password/PasswordList method bodies and a read-only friend probe; hash constructor/hash/insert are extracted unchanged from edited steps.',
                  'Red-black core is assembled from the edited Node/class, insertion and deletion blocks. Iterator extension is inspected separately.',
                  'Binary file tests use only files created inside advanced_checks run directories.',
                  'AddressSanitizer and UndefinedBehaviorSanitizer are enabled for the shared-pointer lifetime regression. LeakSanitizer is disabled because this environment runs under ptrace; leak detection was not validated.']}
(WORK/'advanced_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'failed':report['failed'],'compiled':len(jobs),'changed_steps':len(ids)},ensure_ascii=False))
for item in failed:print('FAILURE',json.dumps(item,ensure_ascii=False))
raise SystemExit(bool(failed))
