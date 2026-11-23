#include <charconv>
#include <iostream>
#include <string>
#include <system_error>

int main() {
    std::string text;
    if (!std::getline(std::cin, text)) {
        std::cout << "INVALID\n";
        return 1;
    }
    long long value{};
    const char* first = text.data();
    const char* last = first + text.size();
    const auto result = std::from_chars(first, last, value);
    if (result.ec != std::errc{} || result.ptr != last) {
        std::cout << "INVALID\n";
        return 1;
    }
    std::cout << value << '\n';
}
