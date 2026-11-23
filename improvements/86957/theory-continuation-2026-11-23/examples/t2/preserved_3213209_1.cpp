#include <cstddef>
#include <iostream>
#include <vector>

int main() {
    std::vector<std::vector<int>> matrix(2, std::vector<int>(3, 0));
    matrix[0][1] = 7;

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0; column < matrix[row].size(); ++column) {
            if (column != 0) {
                std::cout << ' ';
            }
            std::cout << matrix[row][column];
        }
        std::cout << '\n';
    }
}
