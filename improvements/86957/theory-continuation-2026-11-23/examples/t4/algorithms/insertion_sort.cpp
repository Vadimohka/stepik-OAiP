#include <cstddef>
#include <iostream>
#include <vector>

void insertion_sort(std::vector<int>& values) {
    for (std::size_t i = 1; i < values.size(); ++i) {
        const int value = values[i];
        std::size_t position = i;
        while (position > 0 && value < values[position - 1]) {
            values[position] = values[position - 1];
            --position;
        }
        values[position] = value;
    }
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
    insertion_sort(values);
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) {
            std::cout << ' ';
        }
        std::cout << values[i];
    }
    std::cout << '\n';
}
