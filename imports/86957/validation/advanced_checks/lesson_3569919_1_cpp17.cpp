#include <iostream>

// перегрузка функции для работы с аргументами l-values
void fun(const int& lref) {
    std::cout << "l-value reference to const\n";
}

// перегрузка функции для работы с аргументами r-values
void fun(int&& rref) {
    std::cout << "r-value reference\n";
}

int main() {
    int x=7;
    fun(x); // аргумент l-value вызывает функцию с ссылкой l-value
    fun(7); // аргумент r-value вызывает функцию с ссылкой r-value
    return 0;
}
