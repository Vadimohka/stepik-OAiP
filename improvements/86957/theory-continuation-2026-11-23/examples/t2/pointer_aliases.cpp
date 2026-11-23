#include <iostream>
int main() {
    int value{10};
    int copy = value;
    int* first = &value;
    int* second = first;
    *second = 45;
    std::cout << value << ' ' << copy << ' ' << *first << '\n';
    int other{7};
    second = &other;
    *second = 8;
    std::cout << value << ' ' << other << ' ' << *first << '\n';
}
