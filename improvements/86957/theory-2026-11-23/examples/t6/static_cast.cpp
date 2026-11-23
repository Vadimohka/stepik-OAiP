#include <iostream>

int main() {
    const int total = 7;
    const int count = 2;
    const double average = static_cast<double>(total) / count;
    int value = 42;
    void* storage = &value;
    int* same_object = static_cast<int*>(storage);
    std::cout << average << ' ' << *same_object << '\n';
}
