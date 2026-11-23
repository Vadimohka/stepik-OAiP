#include <iostream>

namespace first {
    const int value = 10;
}

namespace second {
    const int value = 20;
}

int main() {
    std::cout << first::value << ' ' << second::value << '\n';
}
