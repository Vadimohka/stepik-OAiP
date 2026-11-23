#include <iostream>

// Contract: -10 <= base <= 10, 0 <= exponent <= 18.
// This interface defines base^0 as 1, including 0^0.
constexpr long long power(long long base, int exponent) {
    long long result = 1;
    for (int i = 0; i < exponent; ++i) {
        result *= base;
    }
    return result;
}

static_assert(power(2, 10) == 1024);
static_assert(power(0, 0) == 1);

int main() {
    long long base = 0;
    int exponent = 0;
    if (!(std::cin >> base >> exponent) || base < -10 || base > 10 ||
        exponent < 0 || exponent > 18) {
        std::cerr << "input error\n";
        return 1;
    }
    std::cout << power(base, exponent) << '\n';
    return 0;
}
