#include <climits>
#include <iostream>
#include <limits>

int main() {
    long double number = 2;
    std::cout << "Bits per byte: " << CHAR_BIT << '\n';
    std::cout << "sizeof(number) = " << sizeof(number) << '\n';
    std::cout << "int range: " << std::numeric_limits<int>::lowest()
              << " ... " << std::numeric_limits<int>::max() << '\n';
}