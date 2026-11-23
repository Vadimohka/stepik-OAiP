#include <cstddef>
#include <iostream>
#include <type_traits>

int main() {
    {
// пример объявления двумерного массива:
int a[5][3];
        static_assert(std::extent_v<decltype(a), 0> == 5);
        static_assert(std::extent_v<decltype(a), 1> == 3);
        // Author wrapper: write every element before reading any element.
        int value = 0;
        for (auto& row : a) {
            for (int& element : row) {
                element = ++value;
            }
        }
        std::cout << a[0][0] << ' ' << a[4][2] << '\n';
    }
    {
// инициализация двумерного массива:
int a[5][3] = { {9, 66, -1}, {3, -3, 30}, {1, 1, 1}, {4, 7, 8}, {5, -5, 0} };
        int total = 0;
        for (const auto& row : a) {
            int row_sum = 0;
            for (int element : row) {
                row_sum += element;
            }
            total += row_sum;
            std::cout << row_sum << ' ';
        }
        std::cout << "total=" << total << '\n';
    }
    {
        // Exact inline example from the same explanatory text.
        int a[2][3]{{1, 2}, {4}};
        for (const auto& row : a) {
            for (int element : row) {
                std::cout << element << ' ';
            }
            std::cout << '\n';
        }
    }
}
