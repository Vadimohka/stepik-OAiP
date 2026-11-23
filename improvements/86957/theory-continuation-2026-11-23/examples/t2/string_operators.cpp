#include <iostream>
#include <string>

int main() {
    std::string first = "ab";
    std::string copy = first;
    copy += "cd";
    const std::string joined = first + "!";
    copy[0] = 'A';
    std::cout << first << '\n' << copy << '\n' << joined << '\n';
    std::cout << std::boolalpha
              << (first == "ab") << ' '
              << (first != copy) << ' '
              << (first < std::string("abc")) << '\n';
}
