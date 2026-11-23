#include <iostream>

// Contract: -1000 <= value <= 1000. Returns twice the value.
int doubled(int value) {
    const int result = 2 * value;
    return result;
}

int main() {
    int value = 0;
    if (!(std::cin >> value) || value < -1000 || value > 1000) {
        std::cerr << "input error\n";
        return 1;
    }
    const int result = doubled(value);
    std::cout << value << ' ' << result << '\n';
    return 0;
}
