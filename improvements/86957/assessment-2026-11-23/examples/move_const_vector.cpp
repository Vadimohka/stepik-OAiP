#include <iostream>
#include <utility>
#include <vector>

int main() {
    const std::vector<int> source{4, 5};
    std::vector<int> destination = std::move(source);
    destination[0] = 1;
    std::cout << source[0] << ' ' << destination[0] << '\n';
}
