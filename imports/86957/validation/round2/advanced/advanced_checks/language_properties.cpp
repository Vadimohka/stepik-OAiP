#include <cassert>
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
