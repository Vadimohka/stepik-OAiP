#include <iostream>

// Contract: -1000 <= a, b <= 1000. Returns their sum.
int sum(int a, int b) {
    return a + b;
}

int main() {
    int a = 0;
    int b = 0;
    if (!(std::cin >> a >> b) || a < -1000 || a > 1000 ||
        b < -1000 || b > 1000) {
        std::cerr << "input error\n";
        return 1;
    }
    const int total = sum(a, b);
    std::cout << total << '\n';
    return 0;
}
