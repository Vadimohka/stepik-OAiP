#include <iostream>

class Base {
public:
    virtual ~Base() {}
};

class Derived : public Base {
public:
    void foo() {
    std::cout << "Derived::foo()" << std::endl; 
    }
};

int main() {
    Derived object;
    Base* p = &object;
    Derived* q = static_cast<Derived*>(p); // преобразование указателя на базовый класс в указатель на производный класс
    q->foo(); // вызов функции foo() из класса Derived
}

