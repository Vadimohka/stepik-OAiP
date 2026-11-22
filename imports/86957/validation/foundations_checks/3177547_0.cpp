#include <cstddef>
#include <iostream>
#include <string>

int main() {
    std::string text;
    std::cout << "Введите строку: ";
    if (!std::getline(std::cin, text)) {
        return 0;
    }

    std::size_t spaces = 0;
    for (char ch : text) {
        if (ch != ' ') {
            continue;
        }
        ++spaces;
    }

    std::cout << spaces << " пробелов\n";
}
