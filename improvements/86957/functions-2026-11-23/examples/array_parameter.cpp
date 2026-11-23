#include <cstddef>
#include <iostream>
#include <iterator>

// Contract: count <= 1000; elements are in [-1000, 1000].
// For count > 0, values points to at least count readable int elements.
// For count == 0, values may be nullptr; the result is 0.
long long sum_array(const int* values, std::size_t count) {
    long long total = 0;
    for (std::size_t i = 0; i < count; ++i) {
        total += values[i];
    }
    return total;
}

int main() {
    int numbers[5]{};
    for (int& value : numbers) {
        if (!(std::cin >> value) || value < -1000 || value > 1000) {
            std::cerr << "input error\n";
            return 1;
        }
    }
    std::cout << sum_array(numbers, std::size(numbers)) << '\n';
    std::cout << sum_array(nullptr, 0) << '\n';
    return 0;
}
