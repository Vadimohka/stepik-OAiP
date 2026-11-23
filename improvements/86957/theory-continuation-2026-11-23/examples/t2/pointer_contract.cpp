#include <cstddef>
#include <iostream>
void set_first(int* data, std::size_t count) {
    if (count != 0) {
        data[0] = 100;
    }
}
int main() {
    int values[]{1, 2, 3};
    set_first(values, 3);
    set_first(nullptr, 0);
    std::cout << values[0] << ' ' << values[1] << '\n';
}
