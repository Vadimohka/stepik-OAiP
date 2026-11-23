#include <cstdlib>
#include <iostream>

int main() {
    int count = 0;
    if (!(std::cin >> count)) {
        std::cerr << "input error\n";
        return EXIT_FAILURE;
    }
    if (count < 0 || count > 1000) {
        std::cerr << "out of range\n";
        return EXIT_FAILURE;
    }
    std::cout << "count: " << count << '\n';
}
