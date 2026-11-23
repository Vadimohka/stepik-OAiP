#include <cstddef>
#include <iostream>
#include <vector>
#include <utility>

void bubble_sort(std::vector<int>& values) {
    for (std::size_t end = values.size(); end > 1; --end) {
        bool swapped = false;
        for (std::size_t i = 1; i < end; ++i) {
            if (values[i] < values[i - 1]) {
                std::swap(values[i], values[i - 1]);
                swapped = true;
            }
        }
        if (!swapped) {
            return;
        }
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
    bubble_sort(values);
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) {
            std::cout << ' ';
        }
        std::cout << values[i];
    }
    std::cout << '\n';
}
