#include <cstddef>
#include <iostream>
#include <vector>

// Contract: at most 20 rows, at most 20 elements in each row;
// each element is in [-1000, 1000]. Empty rows are allowed.
long long sum_matrix(const std::vector<std::vector<int>>& matrix) {
    long long total = 0;
    for (const auto& row : matrix) {
        for (int value : row) {
            total += value;
        }
    }
    return total;
}

int main() {
    int rows = 0;
    int columns = 0;
    if (!(std::cin >> rows >> columns) || rows < 0 || rows > 20 ||
        columns < 0 || columns > 20) {
        std::cerr << "input error\n";
        return 1;
    }
    std::vector<std::vector<int>> matrix(
        static_cast<std::size_t>(rows),
        std::vector<int>(static_cast<std::size_t>(columns)));
    for (auto& row : matrix) {
        for (int& value : row) {
            if (!(std::cin >> value) || value < -1000 || value > 1000) {
                std::cerr << "input error\n";
                return 1;
            }
        }
    }
    std::cout << sum_matrix(matrix) << '\n';
    return 0;
}
