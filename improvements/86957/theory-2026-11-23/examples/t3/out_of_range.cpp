#include <iostream>
#include <stdexcept>
#include <vector>

int main() {
    const std::vector<int> values{10, 20};
    try {
        std::cout << values.at(values.size()) << '\n';
    } catch (const std::out_of_range&) {
        std::cout << "index outside the range\n";
    }
}
