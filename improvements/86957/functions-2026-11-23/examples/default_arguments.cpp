#include <iostream>

// Contract: -1000 <= value, factor <= 1000. Returns their product.
long long scaled(int value, int factor = 3);

int main() {
    int value = 0;
    int factor = 0;
    if (!(std::cin >> value >> factor) || value < -1000 || value > 1000 ||
        factor < -1000 || factor > 1000) {
        std::cerr << "input error\n";
        return 1;
    }
    std::cout << scaled(value) << ' ' << scaled(value, factor) << '\n';
    return 0;
}

long long scaled(int value, int factor) {
    return 1LL * value * factor;
}
