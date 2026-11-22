
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
}
