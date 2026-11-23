#include <iostream>
#include <string>
#include <variant>

int main() {
    std::variant<int, std::string> value{7};
    std::cout << std::get<int>(value) << '\n';
    value = std::string{"ready"};
    if (const auto* text = std::get_if<std::string>(&value)) {
        std::cout << *text << '\n';
    }
    std::cout << std::boolalpha << (std::get_if<int>(&value) == nullptr) << '\n';
    try {
        std::cout << std::get<int>(value) << '\n';
    } catch (const std::bad_variant_access&) {
        std::cout << "wrong alternative\n";
    }
    return 0;
}
