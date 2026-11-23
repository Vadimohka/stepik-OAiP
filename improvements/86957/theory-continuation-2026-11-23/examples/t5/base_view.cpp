#include <iostream>

class Base {
public:
    virtual const char* kind() const { return "Base"; }
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    const char* kind() const override { return "Derived"; }
};

int main() {
    Derived object;
    const Base& view = object;
    Base copy = object;
    std::cout << view.kind() << ' ' << copy.kind() << '\n';
    Base* pointer = &object;
    std::cout << std::boolalpha << (dynamic_cast<Derived*>(pointer) == &object) << '\n';
    Base plain;
    Base* plain_pointer = &plain;
    std::cout << (dynamic_cast<Derived*>(plain_pointer) == nullptr) << '\n';
    return 0;
}
