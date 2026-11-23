#include <cstddef>
#include <iostream>
#include <vector>

std::size_t first_index(const std::vector<int>& values, int key) {
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (values[i] == key) {
            return i;
        }
    }
    return values.size();
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
    const std::size_t position = first_index(values, key);
    if (position == values.size() || values[position] != key) {
        std::cout << "not found\n";
    } else {
        std::cout << position << '\n';
    }
}
