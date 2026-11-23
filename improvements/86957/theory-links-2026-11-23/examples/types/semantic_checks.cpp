#include <cstddef>
#include <iostream>
#include <type_traits>
#include <vector>

int main() {
const int original{7};
auto copy = original;            // int: отдельная изменяемая копия
auto& same = original;           // const int&: ссылка на original
const auto& read_only = copy;    // const int&: чтение copy без копии
copy = 9;
// original == 7, same == 7, read_only == 9

    static_assert(std::is_same_v<decltype(copy), int>);
    static_assert(std::is_same_v<decltype(same), const int&>);
    static_assert(std::is_same_v<decltype(read_only), const int&>);
    static_assert(std::is_same_v<decltype(nullptr), std::nullptr_t>);
    int* empty = nullptr;
    static_assert(std::is_same_v<decltype(empty), int*>);
    const std::vector<int> count_value(3, 0);
    const std::vector<int> elements{3, 0};
    if (empty != nullptr || count_value != std::vector<int>{0, 0, 0}
                         || elements != std::vector<int>({3, 0})) {
        return 1;
    }
    static_assert((2 << 2) == 8 && (16 >> 3) == 2);
    static_assert((5 | 2) == 7 && (6 & 2) == 2 && (5 ^ 2) == 7);
#if __cplusplus >= 202002L
    static_assert((~9) == -10);
    static_assert((-9 >> 1) == -5);
#endif
    std::cout << original << ' ' << same << ' ' << read_only << '\n';
}
