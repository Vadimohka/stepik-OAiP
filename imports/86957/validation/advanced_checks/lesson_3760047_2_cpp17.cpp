#include <iostream>
#include <cstdlib> // для std::exit
#include <clocale>

const int LIMIT = 100; // размер массива

class safearray {
private:
    int arr[LIMIT];
public:
    // обратите внимание, что функция возвращает ссылку!
    int &operator[](int n) {
        if (n < 0 || n >= LIMIT) {
            std::cout << "\nОшибочный индекс!";
            std::exit(1);
        }
        return arr[n];
    }
};

int main() {
    setlocale(LC_ALL, "Russian");
    safearray sa1;
    // задаем значения элементов
    for (int j = 0; j < LIMIT; j++) {
        sa1[j] = j * 10; // используем функцию слева от знака =
    }
    // показываем элементы
    for (int j = 0; j < LIMIT; j++) {
        int temp = sa1[j]; // используем функцию справа от знака =
        std::cout << "Элемент " << j << " равен " << temp << std::endl;
    }
    return 0;
} 
