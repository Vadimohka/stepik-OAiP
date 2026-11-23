#include <cstddef>
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    int n = 0;
    if (!(std::cin >> n) || n < 0 || n > 1000) {
        return 1;
    }
    std::vector<int> values;
    for (int i = 0; i < n; ++i) {
        int value = 0;
        if (!(std::cin >> value)) {
            return 1;
        }
        values.push_back(value);
    }
    int key = 0;
    if (!(std::cin >> key)) {
        return 1;
    }

    std::sort(values.begin(), values.end());
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) {
            std::cout << ' ';
        }
        std::cout << values[i];
    }
    std::cout << '\n';

    const auto it = std::find(values.begin(), values.end(), key);
    std::cout << (it != values.end() ? "found" : "missing") << '\n';
}
