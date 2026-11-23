#include <iostream>

union Floats {
    float f;
    double d;
};

int main() {
    std::cout << "float=" << sizeof(float) << '\n';
    std::cout << "double=" << sizeof(double) << '\n';
    std::cout << "union=" << sizeof(Floats) << '\n';
    std::cout << "alignment=" << alignof(Floats) << '\n';
    return 0;
}
