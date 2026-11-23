#include <iostream>
int main() {
    int a{}, b{};
    if (!(std::cin >> a >> b) || a < -100 || a > 100
                            || b < -100 || b > 100 || b == 0) {
        std::cout << "INVALID\n";
        return 1;
    }
    std::cout << a / b << ' ' << a % b << '\n';
}
