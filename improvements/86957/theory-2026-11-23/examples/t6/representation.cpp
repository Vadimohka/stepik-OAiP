#include <array>
#include <cstring>
#include <iostream>

int main() {
    const unsigned int value = 1;
    std::array<unsigned char, sizeof(value)> bytes{};
    std::memcpy(bytes.data(), &value, sizeof(value));
    std::cout << bytes.size() << '\n';
    for (unsigned char byte : bytes) {
        std::cout << static_cast<unsigned int>(byte) << ' ';
    }
    std::cout << '\n';
}
