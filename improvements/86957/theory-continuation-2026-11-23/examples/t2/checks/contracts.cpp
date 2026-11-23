// Author verification only: no learner exercise or new Stepik step.
#include <array>
#include <cassert>
#include <charconv>
#include <climits>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <system_error>
#include <type_traits>
#include <vector>

int main() {
    int table[2][3]{{1, 2, 3}, {4, 5, 6}};
    static_assert(std::is_same_v<decltype(table), int[2][3]>);
    static_assert(std::is_same_v<decltype(&table[0]), int (*)[3]>);
    static_assert(std::is_same_v<decltype(&table[0][0]), int*>);
    static_assert(sizeof table == 6 * sizeof(int));
    int (*row)[3] = table;
    assert((row + 1)[0][0] == 4);
    assert(-7 / 2 == -3 && -7 % 2 == -1);
    assert(0U - 1U == std::numeric_limits<unsigned int>::max());

    std::array<int, 0> empty{};
    assert(empty.empty() && empty.size() == 0);
    bool thrown = false;
    try { (void)empty.at(0); }
    catch (const std::out_of_range&) { thrown = true; }
    assert(thrown);
    std::vector<int> values;
    values.reserve(8);
    assert(values.empty() && values.capacity() >= 8);
    values.resize(3);
    assert(values[0] == 0 && values[2] == 0);

    std::string text = "ab";
    assert(text[text.size()] == '\0');
    assert(text.substr(text.size()).empty());
    assert(text.find("", text.size()) == text.size());
    assert(text.find("", text.size() + 1) == std::string::npos);
    thrown = false;
    try { (void)text.at(text.size()); }
    catch (const std::out_of_range&) { thrown = true; }
    assert(thrown);
    std::string no_characters(0, 'x');
    assert(no_characters.empty());
    std::string embedded("a\0b", 3);
    assert(embedded.size() == 3 && std::strlen(embedded.c_str()) == 1);

    int number = 7;
    const char only_sign[] = "-";
    auto invalid = std::from_chars(only_sign, only_sign + 1, number);
    assert(invalid.ec == std::errc::invalid_argument);
    assert(invalid.ptr == only_sign && number == 7);
    const char tail[] = "42x";
    auto prefix = std::from_chars(tail, tail + 3, number);
    assert(prefix.ec == std::errc{} && prefix.ptr == tail + 2 && number == 42);
    const char too_large[] = "999999999999999999999999999999999999999999999999999999";
    auto range = std::from_chars(too_large, too_large + sizeof(too_large) - 1, number);
    assert(range.ec == std::errc::result_out_of_range && number == 42);
    std::cout << "{\"char_bit\":" << CHAR_BIT
              << ",\"sizeof_int\":" << sizeof(int)
              << ",\"long_long_digits\":" << std::numeric_limits<long long>::digits
              << ",\"pointer_bytes\":" << sizeof(void*) << "}\n";
}
