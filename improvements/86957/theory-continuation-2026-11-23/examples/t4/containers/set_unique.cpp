#include <iostream>
#include <set>

int main() {
    int n = 0;
    if (!(std::cin >> n) || n < 0 || n > 1000) {
        return 1;
    }
    std::set<int> values;
    for (int i = 0; i < n; ++i) {
        int value = 0;
        if (!(std::cin >> value)) {
            return 1;
        }
        values.insert(value);
    }

    std::cout << values.size() << '\n';
    bool first = true;
    for (int value : values) {
        if (!first) {
            std::cout << ' ';
        }
        std::cout << value;
        first = false;
    }
    std::cout << '\n';
}
