#include <cstdio>

class base_1 {
    int x;
public:
    int y;
};

class base_2 {
    char x[13];
public:
    long y;
};

class base_3 {
    long x;
public:
    long y;
};

class derive : public base_1, public base_2, public base_3 {
    long z;
public:
    long d;
};

int main() {
    printf("\nРазмеры объектов базовых и производного класса\n");
    printf("\n|base_1|=%zu", sizeof(base_1));
    printf("\n|base_2|=%zu", sizeof(base_2));
    printf("\n|base_3|=%zu", sizeof(base_3));
    printf("\n|derive|=%zu", sizeof(derive));

    derive objd, *p_d = &objd;
    base_1 *pb1 = &objd; // Указателю на базовый класс
    base_2 *pb2 = &objd; // можно присвоить значение указателя
    base_3 *pb3 = &objd; // производного класса

    printf("\n\nВыделение объектов базовых классов\n");
    printf("\np_d: %p, %p", static_cast<void*>(p_d), static_cast<void*>(p_d + 1));
    printf("\npb1: %p, %p", static_cast<void*>(pb1), static_cast<void*>(pb1 + 1));
    printf("\npb2: %p, %p", static_cast<void*>(pb2), static_cast<void*>(pb2 + 1));
    printf("\npb3: %p, %p", static_cast<void*>(pb3), static_cast<void*>(pb3 + 1));

    printf("\n\nПолучение адреса производного класса\n");

    p_d = static_cast<derive*>(pb1);
    printf("\np_d и pb1: %p – %p", static_cast<void*>(p_d), static_cast<void*>(pb1));
    p_d = static_cast<derive*>(pb2);
    printf("\np_d и pb2: %p – %p", static_cast<void*>(p_d), static_cast<void*>(pb2));
    p_d = static_cast<derive*>(pb3);
    printf("\np_d и pb3: %p – %p", static_cast<void*>(p_d), static_cast<void*>(pb3));
}
