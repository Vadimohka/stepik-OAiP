
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
}
