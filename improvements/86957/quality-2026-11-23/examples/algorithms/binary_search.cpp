#include <cstddef>
#include <iostream>
#include <vector>
#include <algorithm>

std::size_t lower_bound_index(const std::vector<int>& values, int key) {
    std::size_t left = 0;
    std::size_t right = values.size();
    while (left < right) {
        const std::size_t middle = left + (right - left) / 2;
        if (values[middle] < key) {
            left = middle + 1;
        } else {
            right = middle;
        }
    }
    return left;
}

int main() {
    int n{};
    if (!(std::cin >> n) || n < 0 || n > 1000) {
        return 1;
    }
    std::vector<int> values(static_cast<std::size_t>(n));
    for (int& value : values) {
        if (!(std::cin >> value)) {
            return 1;
        }
    }
    int key{};
    if (!(std::cin >> key)) {
        return 1;
    }
    if (!std::is_sorted(values.begin(), values.end())) {
        return 1;
    }
    const std::size_t position = lower_bound_index(values, key);
    if (position == values.size() || values[position] != key) {
        std::cout << "not found\n";
    } else {
        std::cout << position << '\n';
    }
}
