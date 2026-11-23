#include <iostream>
int main() {
    int table[2][3]{{1, 2, 3}, {4, 5, 6}};
    int (*row)[3] = table;
    std::cout << (*row)[2] << '\n';
    ++row;
    std::cout << (*row)[0] << '\n';
}
