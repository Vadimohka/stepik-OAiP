#include <iostream>

void print_string(const char* str) {
    std::cout << str << std::endl;
}

int main() {
    char str[] = "Hello, world!";
    const char* const_str = const_cast<const char*>(str); // добавление константности
    print_string(const_str); // вызов функции, которая принимает указатель на константный char
    return 0;
}
