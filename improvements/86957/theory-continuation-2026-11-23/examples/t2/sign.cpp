#include <iostream>
int main() {
    int number{};
    if (!(std::cin >> number)) {
        std::cout << "INVALID\n";
        return 1;
    }
    if (number > 0) {
        std::cout << "positive\n";
    } else if (number < 0) {
        std::cout << "negative\n";
    } else {
        std::cout << "zero\n";
    }
    const int nonnegative = number >= 0 ? 1 : 0;
    std::cout << nonnegative << '\n';
}
