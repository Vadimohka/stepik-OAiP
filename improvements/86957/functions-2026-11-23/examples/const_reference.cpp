#include <cstddef>
#include <iostream>
#include <vector>

// Contract: at most 1000 elements; each element is in [-1000, 1000].
// Returns their sum, leaves the vector unchanged; empty sum is 0.
long long sum(const std::vector<int>& numbers) {
    long long total = 0;
    for (int value : numbers) {
        total += value;
    }
    return total;
}

int main() {
    int count = 0;
    if (!(std::cin >> count) || count < 0 || count > 1000) {
        std::cerr << "input error\n";
        return 1;
    }
    std::vector<int> numbers(static_cast<std::size_t>(count));
    for (int& value : numbers) {
        if (!(std::cin >> value) || value < -1000 || value > 1000) {
            std::cerr << "input error\n";
            return 1;
        }
    }
    std::cout << sum(numbers) << ' ' << numbers.size() << '\n';
    return 0;
}
