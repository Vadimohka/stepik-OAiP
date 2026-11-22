#include <iostream>

int main() {
    int values[]{10, 20, 30};
    int* ptr = values;
    std::cout << *ptr << '\n'; // 10
    ++ptr;
    std::cout << *ptr << '\n'; // 20
    --ptr;
    std::cout << *ptr << '\n'; // 10
}