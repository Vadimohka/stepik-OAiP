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
    Base* p = new Derived();
    Derived* q = dynamic_cast<Derived*>(p); // преобразование указателя на базовый класс в указатель на производный класс
    if (q != nullptr) {
        q->foo(); // вызов функции foo() из класса Derived
    } else {
        std::cout << "Invalid cast" << std::endl;
    }
    delete p;
}

