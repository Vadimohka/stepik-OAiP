#include <iostream>
int main() {
    constexpr int rows = 3;
    constexpr int columns = 2;
    const int numbers[rows][columns]{{1, 2}, {3, 4}, {5, 6}};
    for (int row = 0; row < rows; ++row) {
        for (int column = 0; column < columns; ++column) {
            if (column != 0) {
                std::cout << ' ';
            }
            std::cout << numbers[row][column];
        }
        std::cout << '\n';
    }
}
