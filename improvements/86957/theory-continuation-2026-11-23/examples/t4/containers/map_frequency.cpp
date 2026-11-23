#include <iostream>
#include <map>
#include <string>

int main() {
    int n = 0;
    if (!(std::cin >> n) || n < 0 || n > 1000) {
        return 1;
    }
    std::map<std::string, int> counts;
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

    for (const auto& entry : counts) {
        std::cout << entry.first << ' ' << entry.second << '\n';
    }
    const auto it = counts.find(query);
    if (it == counts.end()) {
        std::cout << "not found\n";
    } else {
        std::cout << "count " << it->second << '\n';
    }
    std::cout << "keys " << counts.size() << '\n';
}
