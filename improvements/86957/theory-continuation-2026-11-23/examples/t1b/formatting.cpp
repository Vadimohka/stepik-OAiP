#include <iomanip>
#include <iostream>

int main() {
    std::cout << std::hex << 125 << '\n';
    std::cout << std::dec << 125 << '\n';
    std::cout << std::fixed << std::setprecision(2) << 2.5 << '\n';
    std::cout << std::setfill('0') << std::setw(4) << 7 << ' ' << 8 << '\n';
    std::cout << std::scientific << std::setprecision(4) << 36.234 << '\n';
}
