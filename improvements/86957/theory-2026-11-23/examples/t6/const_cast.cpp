#include <iostream>

int main() {
    int value = 10;
    const int& read_only_view = value;
    int& writable_view = const_cast<int&>(read_only_view);
    writable_view = 12; // The original object is not const.
    std::cout << value << '\n';
    const int immutable = 7;
    const int* pointer = &immutable;
    int* stripped = const_cast<int*>(pointer);
    std::cout << *stripped << '\n'; // Reading is allowed; writing is not.
}
