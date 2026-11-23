#include <iostream>
int main() {
    int values[4]{10, 20, 30, 40};
    int* p = values;
    const auto count = sizeof(values) / sizeof(values[0]);
    p += 2;
    std::cout << count << ' ' << *p << ' ' << p[-1] << '\n';
}
