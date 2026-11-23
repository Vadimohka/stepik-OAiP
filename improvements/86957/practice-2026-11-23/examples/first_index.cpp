#include <algorithm>
#include <iostream>
#include <vector>

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
        const auto it = std::lower_bound(values.begin(), values.end(), key);
        if (it == values.end() || *it != key) {
            std::cout << -1 << '\n';
        } else {
            std::cout << (it - values.begin()) << '\n';
        }
    }
}
