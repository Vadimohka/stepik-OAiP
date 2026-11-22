#include <cassert>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>
#include <type_traits>
int main() {
    static_assert(!std::is_same<int[10], int[16]>::value, "array bounds are part of type");
    int a[4]{}; static_assert(sizeof(a) == 4 * sizeof(int), "array bytes");
    static_assert(std::is_same<decltype(&a), int (*)[4]>::value, "pointer to array");
    char short_copy[3]{};
    std::strncpy(short_copy, "abcdef", 3);
    assert(short_copy[0] == 'a' && short_copy[2] == 'c');
    char padded[5]{'x','x','x','x','x'};
    std::strncpy(padded, "a", 5);
    assert(padded[0] == 'a' && padded[1] == 0 && padded[4] == 0);
    char joined[8] = "ab";
    std::strncat(joined, "cdef", 2);
    assert(std::strcmp(joined, "abcd") == 0 && joined[4] == 0);
    assert(std::isspace('\n') != 0 && std::isspace('\t') != 0);
    assert(std::isalnum(EOF) == 0);
    char high = static_cast<char>(0xFF);
    (void)std::isalnum(static_cast<unsigned char>(high));
    std::string empty;
    assert(empty.size() - 1 == std::numeric_limits<std::string::size_type>::max());
    unsigned count = 0;
    for (std::size_t i = 0; i + 1 < empty.size(); ++i) ++count;
    assert(count == 0);
    bool threw = false;
    try { (void)empty.at(0); } catch (const std::out_of_range&) { threw = true; }
    assert(threw);
    std::string s = "abcdef", t = "012345";
    s.replace(1, 2, t, 3, 2);
    assert(s == "a34def");
    assert(std::string::npos == std::numeric_limits<std::string::size_type>::max());
    std::string interior("a\0b", 3);
    assert(interior.size() == 3 && std::strlen(interior.c_str()) == 1);
}
