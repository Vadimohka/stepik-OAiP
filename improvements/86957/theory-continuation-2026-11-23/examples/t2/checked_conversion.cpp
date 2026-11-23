#include <cmath>
#include <iostream>
int main() {
    double value{};
    if (!(std::cin >> value) || !std::isfinite(value)
                            || value < 0.0 || value > 100.0) {
        std::cout << "INVALID\n";
        return 1;
    }
    const int whole = static_cast<int>(value);
    std::cout << whole << '\n';
}
