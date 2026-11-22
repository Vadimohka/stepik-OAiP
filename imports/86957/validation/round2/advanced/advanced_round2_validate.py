#!/usr/bin/env python3
"""Read-only validation of the round-2 modules 11–20 edits.
Run: python advanced_round2_validate.py --root /path/to/repository
Requires Python 3 and g++ for C++ checks. Baseline fingerprints are bundled.
Artifacts are written beside this script, never into course step files.
"""
import argparse, hashlib, html, json, re, subprocess
from html.parser import HTMLParser
from pathlib import Path

BASE='8bf4639ce2799a13146e22ed13cf103dd1916ad5'
WORK=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path)
parser.add_argument('--structural-only',action='store_true')
parser.add_argument('--case',help='Run only C++ cases matching this regular expression')
args=parser.parse_args()
ROOT=args.root
if ROOT is None:
    ROOT=next((p for p in WORK.parents if (p/'courses/86957/course.json').is_file()),None)
if ROOT is None: parser.error('Pass --root /path/to/repository')
ROOT=ROOT.resolve(); CHECKS=WORK/'advanced_checks';CHECKS.mkdir(exist_ok=True)
log=json.loads((WORK/'advanced.json').read_text())
BASE_DOCS=json.loads((WORK/'advanced_baseline.json').read_text())
assert BASE_DOCS['source_commit']==BASE
bundle=json.loads((ROOT/'courses/86957/course.json').read_text())
sections={s['id']:s['position'] for s in bundle['sections']}
lesson_modules={u['lesson']:sections[u['section']] for u in bundle['units']}
scoped={s['id']:s for s in bundle['steps'] if 11<=lesson_modules[s['lesson']]<=20}
paths={int(p.name.split('_')[1]):p for p in (ROOT/'courses/86957/steps').glob('*/*.step')}
current={sid:json.loads(paths[sid].read_text()) for sid in scoped}
results=[]; cpp_cases=[]
def check(name,ok,detail=''):
    results.append({'name':name,'passed':bool(ok),'detail':detail})
def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def baseline(sid): return BASE_DOCS['steps'][str(sid)]
def getcodes(sid):
    return [html.unescape(x) for x in re.findall(r'<pre><code[^>]*>(.*?)</code></pre>',current[sid]['block']['text'],re.S)]
class Tags(HTMLParser):
    def __init__(self,s):
        super().__init__();self.tags=[];self.feed(s)
    def handle_starttag(self,tag,attrs):self.tags.append(tag)
    def handle_startendtag(self,tag,attrs):self.tags.append(tag)
expected_reviewed={sid for sid,s in scoped.items() if s['block']['name']!='code'}
expected_deferred={sid for sid,s in scoped.items() if s['block']['name']=='code'}
check('coverage_noncode',set(log['reviewed_step_ids'])==expected_reviewed,f'{len(expected_reviewed)} non-code steps')
check('coverage_code_deferred',{x['step_id'] for x in log['deferred']}==expected_deferred,str(sorted(expected_deferred)))
changed=[]; base_docs={}
for sid in sorted(expected_reviewed):
    d=current[sid];b=baseline(sid);base_docs[sid]=b
    check(f'{sid}:metadata', all(d[k]==b['envelope'][k] for k in ['id','time']) and d['block']['name']==b['name'])
    check(f'{sid}:control_characters',not re.search('[\x00-\x08\x0b\x0c\x0e-\x1f]',json.dumps(d,ensure_ascii=False)))
    if sha(canonical(d))==b['document_sha256']: continue
    changed.append(sid)
    check(f'{sid}:only_block_changed',{k:v for k,v in d.items() if k!='block'}==b['envelope'])
    newtext=d['block']['text']
    check(f'{sid}:code_block_count',b['pre_count']==len(re.findall('<pre',newtext)))
    check(f'{sid}:no_new_unknown_html_tags',not (set(Tags(newtext).tags)-set(b['html_tags'])-{'p','code','strong','em','br','h2','h3','h4','ul','ol','li','table','thead','tbody','tr','th','td'}))
    if d['block']['name']=='choice':
        src=d['block']['source'];opts=src['options'];multi=src['is_multiple_choice']
        check(f'{sid}:choice_cardinality',0<sum(o['is_correct'] for o in opts) and (multi or sum(o['is_correct'] for o in opts)==1))
        check(f'{sid}:choice_options_mode',multi==d['block']['options']['is_multiple_choice'] and src['sample_size']<=len(opts))
        check(f'{sid}:choice_keys_preserved',[o['is_correct'] for o in opts]==b['choice_keys'])
        allowed={'code','strong','em','b','i','p','br','span','sub','sup'}
        check(f'{sid}:choice_cpp_escaped',all(not (set(Tags(o['text']).tags)-allowed) for o in opts))
check('findings_steps_changed',all(set(f['step_ids'])<=set(changed) for f in log['findings']))
check('changed_steps_logged',set(changed)=={sid for f in log['findings'] for sid in f['step_ids']})
# Algorithms were reviewed in round 1; verify they were not silently altered in round 2.
for sid in [3570213,3570303,3570304,3570333,3570332,4035443,4035481]:
    before=base_docs[sid]['code_sha256']
    check(f'{sid}:algorithm_excerpts_unchanged',before==[sha(c) for c in getcodes(sid)])

def cpp(name,source,run=True,expected_stdout=None,expect_compile=True):
    if args.case and not re.search(args.case,name): return
    for standard in ['c++17','c++20']:
        ident=name+'_'+standard.replace('+','p');src=CHECKS/(name+'.cpp');exe=CHECKS/ident
        src.write_text(source)
        command=['g++','-std='+standard,'-O0','-Wall','-Wextra','-pedantic',str(src),'-o',str(exe)]
        built=subprocess.run(command,text=True,capture_output=True,timeout=25)
        ok=(built.returncode==0)==expect_compile
        record={'name':ident,'source':src.name,'compile_expected':expect_compile,'compile_returncode':built.returncode,'command':['g++','-std='+standard,'-O0','-Wall','-Wextra','-pedantic','advanced_checks/'+src.name,'-o','advanced_checks/'+ident],'passed':ok}
        report=built.stdout+built.stderr
        if ok and run and expect_compile:
            executed=subprocess.run([str(exe)],cwd=CHECKS,text=True,capture_output=True,timeout=5)
            record.update(run_returncode=executed.returncode,stdout=executed.stdout)
            ok=executed.returncode==0 and (expected_stdout is None or executed.stdout==expected_stdout)
            record['passed']=ok;report+='\nRUN\n'+executed.stdout+executed.stderr
        (CHECKS/(ident+'.log')).write_text(report)
        cpp_cases.append(record);check(ident,ok,('compile/run' if run and expect_compile else 'compile only')+'; '+src.name)

if not args.structural_only:
    cpp('file_positions',r'''#include <cstdio>
#include <cassert>
#include <cstring>
int main() {
 const char* name="round2_file_test.bin";
 FILE* f=std::fopen(name,"w+b");assert(f);
 assert(std::fwrite("abc",1,3,f)==3);
 assert(std::fseek(f,-1,SEEK_END)==0);assert(std::ftell(f)==2);assert(std::fgetc(f)=='c');
 assert(std::fseek(f,0,SEEK_END)==0);assert(std::ftell(f)==3);assert(std::fclose(f)==0);
 f=std::fopen(name,"a+b");assert(f);assert(std::fseek(f,0,SEEK_SET)==0);assert(std::ftell(f)==0);
 assert(std::fputc('D',f)=='D');assert(std::fflush(f)==0);assert(std::fseek(f,0,SEEK_SET)==0);
 char data[5]{};assert(std::fread(data,1,4,f)==4);assert(std::strcmp(data,"abcD")==0);
 assert(std::fclose(f)==0);assert(std::remove(name)==0);
}
''')
    cpp('layout_abi',getcodes(3215232)[0],expected_stdout='sizeof(A) = 8\nsizeof(B) = 8\nsizeof(C) = 8\n')
    cpp('bitfields_printf',getcodes(3216509)[2],expected_stdout='x = 2    y = 5\n')
    uc=getcodes(3215242)
    cpp('union_member_lifetime','#include <cassert>\n'+ '\n'.join(uc[:3])+'\nint main(){\n'+uc[3]+'\nassert(d==3 && T.MP.GetY()==8);\n}\n')
    cpp('const_cast_readonly',getcodes(4047680)[1],expected_stdout='Hello, world!\n')
    cpp('const_cast_adding_const',getcodes(4047680)[2],expected_stdout='Hello, world!\n')
    cpp('language_properties',r'''#include <cassert>
#include <memory>
#include <type_traits>
#include <vector>
struct V {std::vector<int> data;};
struct U {std::unique_ptr<int> data;};
struct UserCtor {explicit UserCtor(int) {}};
struct Zero {int n=0;};
struct Count {inline static int count=0;Count(){++count;}};
struct Base {virtual void f()=0;virtual ~Base()=default;};
struct Mid:Base {};
struct Concrete:Mid {void f() override {}};
struct Inherited:Concrete {};
struct Counter {int value=0;int dummy=-1;Counter operator++(int arg){dummy=arg;auto old=*this;++value;return old;} Counter& operator++(){++value;return *this;}};
struct Array {int data[1]{};int& access(int i){return data[i];} int& operator[](int i){return data[i];}};
struct Sum {int x=0;Sum operator+=(const Sum& b){x+=b.x;return Sum{x};}};
enum E {A=2,B=A,C=-3};
static_assert(!std::is_default_constructible_v<UserCtor>);
static_assert(!std::is_copy_constructible_v<U>);
static_assert(std::is_copy_constructible_v<V>);
static_assert(std::is_abstract_v<Base> && std::is_abstract_v<Mid>);
static_assert(!std::is_abstract_v<Concrete> && !std::is_abstract_v<Inherited>);
static_assert(A==2 && B==2 && C==-3);
int main(){
 V a{{1,2}};V b=a;b.data[0]=8;assert(a.data[0]==1);
 Zero z;assert(z.n==0);Count c1,c2;assert(Count::count==2);
 struct {struct {int x;} inner;} anon{{4}};auto* ap=&anon.inner;ap->x=9;assert(anon.inner.x==9);
 class {public:int x;} unnamed{};unnamed.x=7;assert(unnamed.x==7);
 Counter c;auto old=c++;assert(old.value==0 && c.value==1 && c.dummy==0);
 c.operator++(2);assert(c.dummy==2 && c.value==2);++c;assert(c.value==3);
 Array ar;ar.access(0)=7;assert(ar[0]==7);ar[0]=9;assert(ar.access(0)==9);
 int value=2;int* p=&value;static_assert(std::is_same_v<decltype(*p),int&>);*p=11;assert(value==11);
 Sum x{2},y{3};Sum result=(x+=y);assert(x.x==5 && result.x==5);
 std::vector<Sum> usertypes;usertypes.push_back({4});assert(usertypes[0].x==4);
 assert(5%2==1 && 5%5==0);
}
''')
    cpp('bad_struct_conversion','struct Point{int x,y;};struct Apex{int a,b;};int main(){Point p{1,2};Apex a=(Apex)p;}\n',run=False,expect_compile=False)
    cpp('bad_pointer_member',getcodes(3425979)[0],run=False,expect_compile=False)
    cpp('bad_void_return','struct Distance{};void f(){return Distance{};}int main(){f();}\n',run=False,expect_compile=False)
    cpp('bad_final_base','struct Base final {};struct Derived:Base{};int main(){}\n',run=False,expect_compile=False)
    cpp('bad_incomplete_base','struct Base;struct Derived:Base{};int main(){}\n',run=False,expect_compile=False)
    cpp('bad_arbitrary_c_cast','struct S{int x;};int main(){S s{1};return (int)s;}\n',run=False,expect_compile=False)
    cpp('question_brace_elision',r"""#include <cassert>
struct inner {int f;int g;};
struct s1 {int x;int y;inner in;char* z;};
int main(){
 s1* points=new s1[5];points[0]={1,1,3,4,new char[7]};
 assert(points[0].x==1 && points[0].y==1 && points[0].in.f==3 && points[0].in.g==4);
 inner* p=&points[0].in;assert(p->f==3);
 delete[] points[0].z;delete[] points;
}
""")
    cpp('question_cast_after_printer_fix',getcodes(3425979)[0].replace('inner1.f','inner1->f').replace('inner1.g','inner1->g'),run=False)
    avl_tail=r''' 
#include <cassert>
#include <map>
#include <vector>
#include <climits>
int audit(const std::shared_ptr<Node>& n,long long lo,long long hi,std::map<int,std::string>& values){
 if(!n)return 0;assert(lo<n->key && n->key<hi);
 int l=audit(n->left,lo,n->key,values),r=audit(n->right,n->key,hi,values);
 assert(l-r>=-1 && l-r<=1);assert(n->height==1+std::max(l,r));values.emplace(n->key,n->value);return n->height;
}
void check_tree(const std::shared_ptr<Node>& n,const std::map<int,std::string>& expected){std::map<int,std::string> actual;audit(n,LLONG_MIN,LLONG_MAX,actual);assert(actual==expected);}
int main(){
 for(auto keys:std::vector<std::vector<int>>{{3,2,1},{1,2,3},{3,1,2},{1,3,2}}){
  std::shared_ptr<Node> root;std::map<int,std::string> expected;
  for(int k:keys){root=insert(root,k,std::to_string(k));expected.emplace(k,std::to_string(k));check_tree(root,expected);}
  assert(root->key==2);root=deleteNode(root,2);expected.erase(2);check_tree(root,expected);
 }
 std::shared_ptr<Node> root;std::map<int,std::string> expected;
 for(int k=0;k<40;++k){root=insert(root,k,std::to_string(k));expected.emplace(k,std::to_string(k));check_tree(root,expected);}
 for(int k=0;k<40;k+=2){root=deleteNode(root,k);expected.erase(k);check_tree(root,expected);}
 for(int k=1;k<40;k+=2){root=deleteNode(root,k);expected.erase(k);check_tree(root,expected);}assert(!root);
}
'''
    cpp('avl_rotation_conditions',getcodes(3570281)[0]+avl_tail)

report={'baseline_commit':BASE,'root':'.','reviewed_step_count':len(expected_reviewed),'deferred_code_step_ids':sorted(expected_deferred),'changed_step_ids':changed,'passed':sum(r['passed'] for r in results),'failed':sum(not r['passed'] for r in results),'results':results,'cpp_cases':cpp_cases,'current_step_sha256':{str(sid):hashlib.sha256(paths[sid].read_bytes()).hexdigest() for sid in sorted(expected_reviewed)},'limits':['C++17 and C++20 verified with local GCC; no MSVC execution. Numeric sizes apply only to the stated ABI.','Intentionally invalid syntax is compiled as a negative test; no undefined-behavior examples are executed.','This is targeted verification of round-2 edits; the previous complete algorithm test suite is not rerun.','Video and image pixels were not re-reviewed in this editorial pass; existing diagrams were retained.']}
if cpp_cases:report['compiler']=subprocess.check_output(['g++','--version'],text=True).splitlines()[0]
filename='advanced_structural_validation.json' if args.structural_only else ('advanced_additional_validation.json' if args.case else 'advanced_validation.json')
(WORK/filename).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['reviewed_step_count','passed','failed']},ensure_ascii=False))
print('C++ cases:',len(cpp_cases),'changed steps:',len(changed))
for r in results:
 if not r['passed']:print('FAILED',r)
raise SystemExit(bool(report['failed']))
