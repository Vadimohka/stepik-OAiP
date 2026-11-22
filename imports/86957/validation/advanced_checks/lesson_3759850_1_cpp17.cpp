#include <cstring>
#include <cstdio>

class base_1 {
private:
    int a;
protected:
    int b;
public:
    base_1(int x, int y) { // конструктор base_1
        a = x, b = y;
        printf("\nbase_1: %d%d", a, b);
    }

    ~base_1() { // деструктор base_1
        printf("\n~base_1 (%d,%d)", a, b);
    }

    void print_1() { // отображение объекта класса base_1
        printf("\nbase_1: a=%d b=%d !", a, b);
    }
};

class base_2 {
protected:
    int c;
public:
    base_2(int x) { // конструктор base_2
        c = x;
        printf("\nbase_2: %d", c);
    }

    ~base_2() { // деструктор base_2
        printf("\n~base_2 (%d)", c);
    }

    void print_2() { // отображение объекта класса base_2
        printf("\nbase_2: c=%d !", c);
    }
};

class derive : public base_1, public base_2 {
    int d;
    base_1 e; // элемент вложенного класса
public:
    derive(int x, int y, int z) : // конструктор derive
            base_1(x, y), // связь с конструктором base_1
            base_2(z), // связь с конструктором base_2
            e(x + 1, y + 1) { // связь с конструктором элемента "e"
        d = x;
        printf("\nderive: %d %d %d", d, b, c);
    }

    ~derive() { // деструктор derive
        printf("\n~derive (%d)", d);
    }

    void print_d() { // отображение объекта класса derive
        e.print_1();
        printf(" - derive: d=%d !", d);
    }
};

int main() {
    derive D(1, 2, 3); // определение объекта класса derive
    D.print_1();
    D.print_2();
    D.print_d();
}
