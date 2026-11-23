#include <cstddef>
#include <iostream>
#include <vector>
#include <utility>

void sift_down(std::vector<int>& values, std::size_t root, std::size_t count) {
    while (root < count / 2) {
        std::size_t child = 2 * root + 1;
        if (child + 1 < count && values[child] < values[child + 1]) {
            ++child;
        }
        if (!(values[root] < values[child])) {
            return;
        }
        std::swap(values[root], values[child]);
        root = child;
    }
}

void heap_sort(std::vector<int>& values) {
    for (std::size_t start = values.size() / 2; start > 0; --start) {
        sift_down(values, start - 1, values.size());
    }
    for (std::size_t count = values.size(); count > 1; --count) {
        std::swap(values[0], values[count - 1]);
        sift_down(values, 0, count - 1);
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
    heap_sort(values);
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) {
            std::cout << ' ';
        }
        std::cout << values[i];
    }
    std::cout << '\n';
}
