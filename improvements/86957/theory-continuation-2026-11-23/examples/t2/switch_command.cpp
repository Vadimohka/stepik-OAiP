#include <iostream>
int main() {
    int command{};
    if (!(std::cin >> command)) {
        std::cout << "INVALID\n";
        return 1;
    }
    switch (command) {
        case 1:
            std::cout << "open\n";
            break;
        case 2:
        case 3:
            std::cout << "save\n";
            break;
        default:
            std::cout << "unknown\n";
            break;
    }
}
