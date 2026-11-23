#include <iostream>
#include <vector>

int main() {
    int count{};
    if (!(std::cin >> count) || count < 0 || count > 1000) {
        std::cout << "INVALID\n";
        return 1;
    }

    std::vector<long long> values;
    for (int i = 0; i < count; ++i) {
        long long value{};
        if (!(std::cin >> value) || value < -1000000000LL
                                || value > 1000000000LL) {
            std::cout << "INVALID\n";
            return 1;
        }
        values.push_back(value);
    }

    long long total{};
    for (long long value : values) {
        total += value;
    }
    std::cout << values.size() << ' ' << total << '\n';
}
