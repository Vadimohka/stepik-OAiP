#include <iostream>

// Contract: 0 <= n <= 20. Returns n!, including 0! = 1.
unsigned long long factorial(unsigned int n) {
    if (n == 0) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main() {
    int n = 0;
    if (!(std::cin >> n) || n < 0 || n > 20) {
        std::cerr << "input error\n";
        return 1;
    }
    std::cout << factorial(static_cast<unsigned int>(n)) << '\n';
    return 0;
}
