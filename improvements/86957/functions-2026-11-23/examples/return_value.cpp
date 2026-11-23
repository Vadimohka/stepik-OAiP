#include <iostream>

// Contract: -1000 <= value <= 1000. Returns value squared.
long long square(int value) {
    const long long result = 1LL * value * value;
    return result;
}

int main() {
    int value = 0;
    if (!(std::cin >> value) || value < -1000 || value > 1000) {
        std::cerr << "input error\n";
        return 1;
    }
    const long long answer = square(value);
    std::cout << answer << '\n';
    return 0;
}
