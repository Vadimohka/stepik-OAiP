#include <iostream>
int main() {
    int before{};
    while (before < 0) {
        ++before;
    }
    int after{};
    do {
        ++after;
    } while (after < 0);
    std::cout << before << ' ' << after << '\n';
}
