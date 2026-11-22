#include <cstddef>
#include <iostream>
#include <new>

int main() {
    const std::size_t veryBigSize = 1000000000;
    // int automaticArray[veryBigSize]; // такой объект может переполнить стек
    try {
        int* dynamicArray = new int[veryBigSize];
        // Работа с массивом — только после успешного выделения.
        delete[] dynamicArray;
    } catch (const std::bad_alloc&) {
        std::cerr << "Cannot allocate the array\n";
        return 1;
    }
}
