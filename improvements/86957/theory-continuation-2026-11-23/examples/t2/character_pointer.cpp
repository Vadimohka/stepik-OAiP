#include <iostream>
int main() {
    char letters[] = "hello";
    char* p = letters;
    std::cout << p << '\n';
    std::cout << *p << '\n';
    p += 2;
    std::cout << p << '\n';
}
