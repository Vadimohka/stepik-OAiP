#include <iostream>

int main() {
    char c = 'N';
    char* pc = &c;
    std::cout << "address=" << static_cast<const void*>(pc) << '\n';
    std::cout << "character=" << *pc << '\n';
    const char text[] = "N";
    std::cout << "string=" << text << '\n';
}