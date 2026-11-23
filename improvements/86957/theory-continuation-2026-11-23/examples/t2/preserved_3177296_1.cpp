#include <array>
#include <iostream>

int main() {
    const std::array<int, 4> scores{10, 20, 15, 5};
    int total{};
    for (int score : scores) {
        total += score;
    }
    std::cout << scores.size() << ' ' << total << '\n';
}
