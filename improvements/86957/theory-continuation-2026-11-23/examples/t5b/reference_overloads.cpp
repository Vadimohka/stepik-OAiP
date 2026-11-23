#include <iostream>
#include <utility>

void inspect(const int& value) {
    std::cout << "const lvalue reference: " << value << '\n';
}

void inspect(int&& value) {
    std::cout << "rvalue reference: " << value << '\n';
}

int main() {
    int x{7};
    const int cx{9};
    int&& named = 8;
    inspect(x);
    inspect(7);
    inspect(named);
    inspect(std::move(named));
    inspect(std::move(cx));
    std::cout << x << ' ' << named << ' ' << cx << '\n';
}
