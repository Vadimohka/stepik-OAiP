#include <iostream>
#include <map>
#include <string>

int main() {
    const std::map<int, std::string> labels{{20, "B"}, {10, "A"}, {30, "C"}};
    for (auto it = labels.begin(); it != labels.end(); ++it) {
        std::cout << it->first << ':' << it->second << ' ';
    }
    std::cout << '\n';
    auto last = labels.end();
    if (!labels.empty()) {
        --last;
        std::cout << last->first << '\n';
    }
}
