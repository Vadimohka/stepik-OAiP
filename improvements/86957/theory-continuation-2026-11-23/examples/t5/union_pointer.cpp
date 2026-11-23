#include <iostream>

union Number {
    int integer;
    double real;
};

int main() {
    Number number{4};
    Number* pointer = &number;
    std::cout << pointer->integer << '\n';
    pointer->real = 1.25;
    std::cout << number.real << '\n';
    return 0;
}
