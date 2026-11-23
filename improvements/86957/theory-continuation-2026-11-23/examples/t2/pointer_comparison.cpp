#include <iostream>
int main() {
    int values[]{10, 20};
    int* first = &values[0];
    int* same = first;
    int* second = &values[1];
    std::cout << std::boolalpha << (first == same) << ' '
              << (first < second) << '\n';
}
