#include <iostream>

int main() {
    int n{};
    int m{};
    if (!(std::cin >> n >> m) || n < 0 || n > 1000 || m < 0 || m > 1000) {
        return 1;
    }
    long long sequential{};
    for (int i = 0; i < n; ++i) {
        ++sequential;
    }
    for (int j = 0; j < m; ++j) {
        ++sequential;
    }
    long long triangle{};
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < i; ++j) {
            ++triangle;
        }
    }
    long long rectangle{};
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < m; ++j) {
            ++rectangle;
        }
    }
    std::cout << "sequential=" << sequential << '\n';
    std::cout << "triangle=" << triangle << '\n';
    std::cout << "rectangle=" << rectangle << '\n';
}
