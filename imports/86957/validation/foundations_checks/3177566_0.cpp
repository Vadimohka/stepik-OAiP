#include <iostream>

int main() {
    int n{};
    std::cin >> n;
    int i = 1;
    while (i < n) {
        std::cout << i << " * " << i << " = " << 1LL * i * i << '\n';
        ++i;
    }
    return 0;
}
