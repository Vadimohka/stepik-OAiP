#include <iostream>
#include <vector>

std::vector<int> make_values() {
    std::vector<int> values{10, 20, 30};
    return values;
}

int main() {
    const std::vector<int> values = make_values();
    std::cout << values.size() << ' ' << values[1] << '\n';
}
