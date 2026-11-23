#include <cstddef>
#include <iostream>
#include <string>
#include <unordered_map>

int main() {
    int n = 0;
    if (!(std::cin >> n) || n < 0 || n > 1000) {
        return 1;
    }
    std::unordered_map<std::string, int> counts;
    counts.reserve(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) {
        std::string word;
        if (!(std::cin >> word)) {
            return 1;
        }
        ++counts[word];
    }
    std::string query;
    if (!(std::cin >> query)) {
        return 1;
    }

    const auto it = counts.find(query);
    if (it == counts.end()) {
        std::cout << "not found\n";
    } else {
        std::cout << "count " << it->second << '\n';
    }
    std::cout << "keys " << counts.size() << '\n';
}
