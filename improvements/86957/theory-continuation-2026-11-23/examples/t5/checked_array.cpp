#include <array>
#include <cstddef>
#include <iostream>
#include <stdexcept>

class CheckedArray {
    std::array<int, 4> data_{};
public:
    int& operator[](std::size_t index) {
        return data_.at(index);
    }
    const int& operator[](std::size_t index) const {
        return data_.at(index);
    }
};

int main() {
    CheckedArray values;
    values[0] = 10;
    values[3] = 30;
    const CheckedArray& view = values;
    std::cout << view[0] << ' ' << view[1] << ' ' << view[3] << '\n';
    try {
        values[4] = 99;
    } catch (const std::out_of_range&) {
        std::cout << "index error\n";
    }
    std::cout << view[3] << '\n';
    return 0;
}
