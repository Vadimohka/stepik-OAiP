#include <iostream>
int main() {
    int value{10};
    int* pointer = &value;
    std::cout << *pointer << '\n';
    *pointer = 25;
    std::cout << value << '\n';
    pointer = nullptr;
    std::cout << std::boolalpha << (pointer == nullptr) << '\n';
}
