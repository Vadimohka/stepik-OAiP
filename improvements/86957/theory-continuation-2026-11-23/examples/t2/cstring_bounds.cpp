#include <cstring>
#include <iostream>

int main() {
    char word[8] = "cat";
    const char data[] = {'A', '\0', 'B', '\0'};
    std::cout << std::strlen(word) << ' ' << sizeof word << '\n';
    std::cout << std::strlen(data) << ' ' << sizeof data << '\n';
}
