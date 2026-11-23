// Author-only checks; this file is not a learner task or a course listing.
#include <cassert>
#include <climits>
#include <iostream>
#include <limits>
#include <type_traits>

int main() {
    static_assert(std::is_same_v<decltype(0U - 1U), unsigned int>);
    assert(0U - 1U == std::numeric_limits<unsigned int>::max());

    unsigned char zero{};
    constexpr bool fits_int = std::numeric_limits<unsigned char>::max()
        <= std::numeric_limits<int>::max();
    using Promoted = decltype(zero - 1);
    static_assert(std::is_same_v<Promoted,
        std::conditional_t<fits_int, int, unsigned int>>);
    const Promoted expected = []() -> Promoted {
        if constexpr (fits_int) {
            return static_cast<Promoted>(-1);
        } else {
            return std::numeric_limits<Promoted>::max();
        }
    }();
    assert(zero - 1 == expected);

    int pairs{};
    for (int a = -100; a <= 100; ++a) {
        for (int b = -100; b <= 100; ++b) {
            if (b == 0) {
                continue;
            }
            const int q = a / b;
            const int r = a % b;
            assert(q * b + r == a);
            assert(r == 0 || (r > 0) == (a > 0));
            assert(r < (b > 0 ? b : -b));
            assert(r > -(b > 0 ? b : -b));
            ++pairs;
        }
    }
    assert(-7 / 2 == -3);
    assert(-7 % 2 == -1);
    // Check the platform assumption before compiling the separate rejected
    // constant-expression fixtures. No undefined arithmetic is executed here.
    assert(std::numeric_limits<int>::min() + std::numeric_limits<int>::max() == -1);
    std::cout << "{\"int_min\":" << std::numeric_limits<int>::min()
              << ",\"int_max\":" << std::numeric_limits<int>::max()
              << ",\"char_bit\":" << CHAR_BIT
              << ",\"long_double_bytes\":" << sizeof(long double)
              << ",\"uchar_promotes_to_int\":" << (fits_int ? "true" : "false")
              << ",\"valid_division_pairs\":" << pairs << "}\n";
}
