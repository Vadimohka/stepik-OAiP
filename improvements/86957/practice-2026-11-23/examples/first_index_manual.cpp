#include <iostream>
#include <vector>

int first_index(const std::vector<int>& values, int key) {
    int left = 0;
    int right = static_cast<int>(values.size());
    while (left < right) {
        const int middle = left + (right - left) / 2;
        if (values[static_cast<std::size_t>(middle)] < key) {
            left = middle + 1;
        } else {
            right = middle;
        }
    }
    if (left == static_cast<int>(values.size()) ||
        values[static_cast<std::size_t>(left)] != key) {
        return -1;
    }
    return left;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    int n = 0;
    int q = 0;
    if (!(std::cin >> n >> q) || n < 0 || n > 100000 || q < 0 || q > 100000) {
        return 1;
    }
    std::vector<int> values(static_cast<std::size_t>(n));
    for (int& value : values) {
        if (!(std::cin >> value)) {
            return 1;
        }
    }
    for (int query = 0; query < q; ++query) {
        int key = 0;
        if (!(std::cin >> key)) {
            return 1;
        }
        std::cout << first_index(values, key) << '\n';
    }
}
