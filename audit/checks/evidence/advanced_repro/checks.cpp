#include <cassert>
#include <cstdio>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <type_traits>
#include <utility>

struct inner { bool x; char z; int y; };
#pragma pack(push, 2)
struct T { int i; short j; double k; inner in; };
#pragma pack(pop)
union Padding { char bytes[5]; int value; };
union PrivateUnion {
private: int i;
public: PrivateUnion() : i(1) {} int get() const { return i; }
};
struct Named { Named* next = nullptr; };
enum Small { Zero, One };
struct Bits { bool b:1; unsigned char c:3; Small e:1; unsigned long long wide:70; };
struct Owner { std::unique_ptr<int> p; };
struct Base { int x; explicit Base(int n) : x(n) {} };
struct Derived : Base { using Base::Base; };
std::string order;
struct B1 { B1() { order += "1"; } };
struct B2 { B2() { order += "2"; } };
struct D : B1, B2 { D() : B2(), B1() { order += "D"; } };
struct Poly { virtual ~Poly() = default; };
struct Sub : Poly {};

int main() {
    const char* path = "advanced-repro-absent.txt";
    std::remove(path);
    std::fstream file(path);
    file << "ABOBA";
    std::cout << "fstream_absent_open=" << file.is_open() << '\n';
    assert(!file.is_open());
    static_assert(std::is_same_v<decltype(std::declval<std::ofstream&>() << 1), std::ostream&>);
    FILE* fp = std::fopen("advanced-repro-io.bin", "w+b");
    assert(fp);
    int values[2] = {1, 2};
    auto written = std::fwrite(values, sizeof(int), 2, fp);
    std::cout << "fwrite_elements=" << written << ", bytes=" << std::ftell(fp) << '\n';
    std::rewind(fp);
    int read_values[2]{};
    auto read = std::fread(read_values, sizeof(int), 2, fp);
    assert(read == 2 && written == 2);
    std::fclose(fp);
    std::remove("advanced-repro-io.bin");
    std::cout << "sizes_inner_T=" << sizeof(inner) << ',' << sizeof(T) << '\n';
    std::cout << "union_size_vs_max=" << sizeof(Padding) << ',' << sizeof(Padding::bytes) << '\n';
    assert(sizeof(inner) == 8 && sizeof(T) == 22);
    assert(sizeof(Padding) > 5);
    PrivateUnion u; assert(u.get() == 1);
    Named n; assert(n.next == nullptr);
    class Local { public: int n = 1; }; Local local; assert(local.n == 1);
    Bits bits{}; bits.b = true; bits.c = 3; bits.e = One; bits.wide = 5;
    Derived derived(7); assert(derived.x == 7);
    D d; std::cout << "base_order=" << order << '\n'; assert(order == "12D");
    const int& literal = 5; assert(literal == 5);
    int x = 7; int&& rr = std::move(x); rr = 8;
    assert(&rr == &x && x == 8);
    std::string{} = "modifiable temporary";
    Owner one{std::make_unique<int>(5)};
    Owner two = std::move(one);
    std::cout << "implicit_move=" << bool(one.p) << ',' << *two.p << '\n';
    assert(!one.p && *two.p == 5);
    std::weak_ptr<int> weak;
    { auto shared = std::make_shared<int>(1); weak = shared; }
    assert(weak.expired() && !weak.lock());
    std::deque<int> deque(1024);
    std::size_t gaps = 0;
    for (std::size_t i = 1; i < deque.size(); ++i) {
        auto prev = reinterpret_cast<std::uintptr_t>(&deque[i - 1]);
        auto curr = reinterpret_cast<std::uintptr_t>(&deque[i]);
        gaps += curr != prev + sizeof(int);
    }
    std::cout << "deque_nonadjacent_pairs=" << gaps << '\n';
    assert(gaps > 0);
    Poly base;
    bool caught = false;
    try { (void)dynamic_cast<Sub&>(base); }
    catch (const std::bad_cast&) { caught = true; }
    assert(caught);
    std::cout << "all_safe_checks_passed\n";
}
