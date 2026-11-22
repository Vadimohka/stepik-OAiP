#include <iostream>
#include <string>

int main() {
    std::string text;
    if (!std::getline(std::cin, text)) {
        return 1;
    }
    const auto position = text.find(':');
    if (position == std::string::npos) {
        std::cout << "NO_SEPARATOR\n";
        return 0;
    }
    const std::string key = text.substr(0, position);
    const std::string value = text.substr(position + 1);
    std::cout << key << '\n' << value << '\n';
}
