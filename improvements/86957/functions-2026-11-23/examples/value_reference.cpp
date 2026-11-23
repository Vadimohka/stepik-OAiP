#include <iostream>

// Both functions require -1000 <= value <= 1000.
int incremented(int value) {
    value += 1;
    return value;
}

void increment(int& value) {
    value += 1;
}

int main() {
    int value = 0;
    if (!(std::cin >> value) || value < -1000 || value > 1000) {
        std::cerr << "input error\n";
        return 1;
    }
    const int next = incremented(value);
    std::cout << value << ' ' << next << '\n';
    increment(value);
    std::cout << value << '\n';
    return 0;
}
