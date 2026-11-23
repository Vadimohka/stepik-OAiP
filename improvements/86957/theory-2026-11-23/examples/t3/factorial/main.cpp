#include "factorial.hpp"
#include <iostream>

int main() {
    int n = 0;
    if (!(std::cin >> n) || n < 0 || n > static_cast<int>(factorial_limit)) {
        std::cerr << "input error\n";
        return 1;
    }
    std::cout << factorial(static_cast<unsigned int>(n)) << '\n';
}
