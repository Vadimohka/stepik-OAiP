#include <iostream>
int main() {
int values[]{10, 20, 30};
int* p = &values[1];
std::cout << p[-1]; // 10: предыдущий элемент того же массива
}
