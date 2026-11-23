#include <iostream>

union Number {
    int integer;
    double real;
};

int main() {
    Number number{7};
    std::cout << number.integer << '\n';
    number.real = 2.5;
    std::cout << number.real << '\n';
    return 0;
}
