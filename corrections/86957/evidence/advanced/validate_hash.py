"""Reproduce exception paths of the two published HashTable methods.

The lesson intentionally omits Password/PasswordList method definitions. The
fixture supplies a conventional append-only chain matching those declarations.
Constructor tests use a small allocation-counting PasswordList fixture to
inject bad_alloc into operator new at an exact list-allocation site.
"""
import json
from course_blocks import blocks
from validate_advanced import HERE, compile_case, execute, results

ALLOC = r'''
#include <cstdlib>
#include <cstdio>
#include <new>
#include <string>
int arrays=0, lists=0, attempt=0, fail_at=0;
void* operator new[](std::size_t n) {
    if(void* p=std::malloc(n)) { ++arrays; return p; }
    throw std::bad_alloc{};
}
void operator delete[](void* p) noexcept { if(p) --arrays; std::free(p); }
void operator delete[](void* p,std::size_t) noexcept { ::operator delete[](p); }
struct PasswordList {
    static void* operator new(std::size_t n) {
        if(++attempt==fail_at) throw std::bad_alloc{};
        if(void* p=std::malloc(n)) { ++lists; return p; }
        throw std::bad_alloc{};
    }
    static void operator delete(void* p) noexcept { if(p) --lists; std::free(p); }
};
'''
DTOR = r'''
HashTable::~HashTable() {
    for(int i=0;i<tableSize;++i) delete items[i];
    delete[] items;
}
'''
CONSTRUCTOR_TEST = r'''
int main(int argc,char** argv) {
    fail_at=argc>1 ? std::atoi(argv[1]) : 3;
    try { HashTable table(5); } catch(const std::bad_alloc&) {}
    std::printf("live arrays=%d, live lists=%d\n",arrays,lists);
    return arrays==0 && lists==0 ? 0 : 3;
}
'''
METHODS = r'''
bool fail_password=false;
Password::Password(int id,std::string descriptionInput,std::string passwordInput)
    : ID(id),description(descriptionInput),password(passwordInput) {
    if(fail_password) throw std::bad_alloc{};
}
int Password::GetID(){return ID;}
std::string Password::GetDescription(){return description;}
std::string Password::GetPassword(){return password;}
void Password::SetDescription(std::string s){description=s;}
void Password::SetPassword(std::string s){password=s;}
PasswordList::PasswordList():count(0){}
std::shared_ptr<Password> PasswordList::GetHead(){return head;}
int PasswordList::GetCount(){return count;}
void PasswordList::AddElement(std::shared_ptr<Password> p){
    if(tail) tail->nextElement=p; else head=p;
    tail=p; ++count;
}
std::shared_ptr<Password> PasswordList::SearchElementByID(int id){
    auto p=head;
    while(p && p->GetID()!=id) p=p->nextElement;
    return p;
}
float HashTable::CalculateNumberOfElements(){
    int total=0;for(int i=0;i<tableSize;++i) total+=items[i]->GetCount();
    return static_cast<float>(total);
}
'''
INSERT_TEST = r'''
#include <cassert>
#include <iostream>
int main(){
    HashTable table(1);
    fail_password=true;
    try { table.InsertElement(1,"first","secret"); assert(false); }
    catch(const std::bad_alloc&) {}
    std::cout << "after failed insert: buckets=" << table.BucketCount()
              << ", entries=" << table.CalculateNumberOfElements() << '\n';
    if(table.BucketCount()!=0 || table.CalculateNumberOfElements()!=0) return 4;
    fail_password=false;
    table.InsertElement(1,"first","secret");
    table.InsertElement(2,"collision","other");
    table.InsertElement(1,"updated","new secret");
    assert(table.BucketCount()==1 && table.CalculateNumberOfElements()==2);
    assert(table.Lookup(1)->GetPassword()=="new secret");
    assert(table.Lookup(2)->GetPassword()=="other");
    std::cout << "successful inserts, collision and duplicate update passed\n";
}
'''

if __name__=='__main__':
    try:
        declaration=blocks(4035443)[2]
        for corrected in (False,True):
            label='after' if corrected else 'before'
            for std in ('c++17','c++20'):
                s=ALLOC+declaration+blocks(4035481,corrected)[0]+DTOR+CONSTRUCTOR_TEST
                exe,_=compile_case('4035481_ctor_'+label+'_'+std,s,std,sanitize=True)
                execute('4035481_ctor_'+label+'_'+std,exe,expected=0 if corrected else 3,
                        contains='live arrays=0, live lists=0' if corrected else 'live arrays=1, live lists=2')
                # Valid positive construction and destruction, using the same executable.
                from validate_advanced import run
                r=run([str(exe),'0']); assert r.returncode==0, r.stderr
                results.append({'case':'4035481_ctor_success_'+label+'_'+std,'phase':'run','returncode':r.returncode,'stdout':r.stdout})
        declaration=declaration.replace('    HashTable(int tableSize);', '''    HashTable(int tableSize);
    int BucketCount() const { return tableCount; } // test-only observation
    std::shared_ptr<Password> Lookup(int k) { return items[CalculateHash(k)]->SearchElementByID(k); }
''')
        for corrected in (False,True):
            label='after' if corrected else 'before'
            s='#include <memory>\n#include <string>\n#include <new>\n'+ '\n'.join(blocks(4035443)[:2])+declaration+METHODS
            s+='\n'.join(blocks(4035481,corrected))+DTOR+INSERT_TEST
            exe,_=compile_case('4035481_insert_'+label,s,sanitize=True)
            execute('4035481_insert_'+label,exe,expected=0 if corrected else 4,
                    contains='buckets=0, entries=0' if corrected else 'buckets=1, entries=0')
    finally:
        (HERE/'hash_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print('Passed hash exception-path checks:',len(results))
