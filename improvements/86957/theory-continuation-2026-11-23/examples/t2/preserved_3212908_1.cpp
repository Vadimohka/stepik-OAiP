#include <array>
#include <iostream>

int main() {
    int raw[4]{1, 2};
    const std::array<int, 4> original{1, 2};
    std::array<int, 4> copy = original;
    copy[0] = 9;

    std::cout << raw[0] << ' ' << raw[3] << '\n';
    std::cout << copy[0] << ' ' << copy[3] << '\n';
}
