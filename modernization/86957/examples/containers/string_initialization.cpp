#include <iostream>
#include <string>

int main() {
    const std::string source = "abcdef";
    std::string empty;
    std::string copy = source;
    copy[0] = 'A';
    const std::string repeated(3, 'x');
    const std::string one_character(1, 'x');
    const std::string part(source, 1, 2);

    std::cout << empty.empty() << '\n';
    std::cout << source << '\n' << copy << '\n';
    std::cout << repeated << '\n' << one_character << '\n' << part << '\n';
}
