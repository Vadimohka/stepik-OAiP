#include <clocale>
#include <iostream>

int main() {
    std::setlocale(LC_ALL, "russian");

    int x = 5;
    int y = 3;
    char sign{};

    std::cout << "Введите знак операции: ";
    if (!(std::cin >> sign)) {
        return 1;
    }

    int result = sign=='+'?x + y:x - y;

    std::cout << "Результат: " << result << "\n";
    return 0;
}
