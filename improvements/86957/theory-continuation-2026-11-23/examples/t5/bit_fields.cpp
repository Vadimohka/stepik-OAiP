#include <iostream>

struct Flags {
    unsigned x : 5;
    unsigned y : 3;
};

int main() {
    Flags flags{2, 5};
    std::cout << flags.x << ' ' << flags.y << '\n';
    flags.x = 31;
    flags.y = 7;
    std::cout << flags.x << ' ' << flags.y << '\n';
    return 0;
}
