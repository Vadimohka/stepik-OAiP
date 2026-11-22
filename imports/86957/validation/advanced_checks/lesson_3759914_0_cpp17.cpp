#include <cstdio>
class base { // абстрактный класс
public:
    virtual void f()= 0; // строго виртуальная функция
};

class derive_1 : public base {
public:
    void f() {
        printf("\nderive_1");
    }
};

class derive_2 : public base {
public:
    void f() { 
        printf("\nderive_2");
    }
};

class derive12 : public derive_1 {
public:
    void f() {
        printf("\nderive12");
    }
};

int main() {
    derive_1 D_1;
    derive_2 D_2;
    derive12 D12;
    base *pb;
    pb=&D_1;
    pb->f(); // Выбор функции класса derive_1
    pb=&D_2;
    pb->f(); // Выбор функции класса derive_2
    pb=&D12;
    pb->f(); // Выбор функции класса derive12
}
