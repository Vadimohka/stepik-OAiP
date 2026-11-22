#include <iostream>

void print_string(char* str) {
    std::cout << str << std::endl;
}

int main() {
    const char* const_str = "Hello, world!";
    char* str = const_cast<char*>(const_str); // удаление константности
    print_string(str); // вызов функции, которая принимает указатель на не константный char
    return 0;
}
