#include <iostream>

int main() {
    long long n{};
    if (!(std::cin >> n) || n < 1 || n > 1'000'000'000) {
        return 1;
    }
    int divisions{};
    while (n > 1) {
        n /= 2;
        ++divisions;
    }
    std::cout << divisions << '\n';
}
