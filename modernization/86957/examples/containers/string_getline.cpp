#include <iostream>
#include <string>

int main() {
    std::string text;
    if (!std::getline(std::cin, text)) {
        return 1;
    }
    std::cout << text.size() << '\n' << text << '\n';
}
