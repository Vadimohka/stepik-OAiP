#include <iostream>

struct Identity {
    int id;
    explicit Identity(int value) : id(value) {}
};

struct Scanner : virtual public Identity {
    Scanner() : Identity(1) {}
};

struct Printer : virtual public Identity {
    Printer() : Identity(2) {}
};

struct Combined : public Scanner, public Printer {
    explicit Combined(int value) : Identity(value), Scanner(), Printer() {}
};

int main() {
    Combined device{42};
    Scanner& scanner = device;
    Printer& printer = device;
    Identity* first = &scanner;
    Identity* second = &printer;
    std::cout << device.id << '\n';
    std::cout << std::boolalpha << (first == second) << '\n';
    Scanner standalone;
    std::cout << standalone.id << '\n';
    return 0;
}
