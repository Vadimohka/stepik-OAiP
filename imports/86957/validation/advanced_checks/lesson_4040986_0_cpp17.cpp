#include <iostream>
#include <utility>
#include <vector>

int main() {
    std::vector<int> v1{1, 2, 3};
    std::vector<int> v2 = std::move(v1); // перемещение v1 в v2

    std::cout << v1.size() << std::endl; // допустимо; состояние v1 после перемещения не следует угадывать
    std::cout << v2.size() << std::endl; // 3

    return 0;
}
