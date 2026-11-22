#include <iostream>
#include <vector>

int main() {
    std::vector<int> values;
    values.reserve(8);
    std::cout << values.size() << ' ' << (values.capacity() >= 8) << '\n';

    values.resize(3);
    values[2] = 7;
    std::cout << values.size() << ' ' << values[2] << '\n';

    std::vector<int> copy = values;
    copy[0] = 1;
    std::cout << values[0] << ' ' << copy[0] << '\n';
}
