#include <cstddef>
#include <iostream>

struct Record {
    char tag;
    int value;
};

int main() {
    std::cout << "char=" << sizeof(char) << '\n';
    std::cout << "int=" << sizeof(int) << '\n';
    std::cout << "record=" << sizeof(Record) << '\n';
    std::cout << "alignment=" << alignof(Record) << '\n';
    std::cout << "value_offset=" << offsetof(Record, value) << '\n';
    return 0;
}
