#include "interesting.hpp"
#include <iostream>

int main() {
    long long n{};
    if (!(std::cin >> n) || n < 1 || n > 1'000'000'000) {
        std::cerr << "Expected an integer from 1 to 1000000000\n";
        return 1;
    }
    std::cout << CountInterestingInInterval(n) << '\n';
}
