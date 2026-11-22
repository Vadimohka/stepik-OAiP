#include <array>
#include <iostream>

int main() {
    constexpr int count = 4;
    const std::array<int, count> values{10, 20, 30, 40};
    int index{};
    if (!(std::cin >> index) || index < 0 || index >= count) {
        std::cout << "INVALID\n";
        return 0;
    }
    std::cout << values[index] << '\n';
}
