#include <iostream>
#include <stdexcept>

struct BaseA {
    BaseA() { std::cout << "BaseA\n"; }
    ~BaseA() { std::cout << "~BaseA\n"; }
};
struct BaseB {
    BaseB() { std::cout << "BaseB\n"; }
    ~BaseB() { std::cout << "~BaseB\n"; }
};
struct Member {
    Member() { std::cout << "Member\n"; }
    ~Member() { std::cout << "~Member\n"; }
};

class Derived : public BaseA, public BaseB {
    Member member_;
public:
    explicit Derived(bool fail) : BaseA(), BaseB(), member_() {
        std::cout << "Derived body\n";
        if (fail) throw std::runtime_error("construction");
    }
    ~Derived() { std::cout << "~Derived body\n"; }
};

int main() {
    {
        Derived complete{false};
    }
    std::cout << "failed construction\n";
    try {
        Derived incomplete{true};
    } catch (const std::runtime_error&) {
        std::cout << "caught\n";
    }
    return 0;
}
