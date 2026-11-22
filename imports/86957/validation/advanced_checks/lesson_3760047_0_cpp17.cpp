#include <iostream>
#include <cstdlib> // для std::exit
#include <clocale>

const int LIMIT = 100; // размер массива

class safearray {
private:
    int arr[LIMIT];
public:
    // установка значения элемента массива
    void putel(int n, int elvalue) {
        if (n < 0 || n >= LIMIT) {
            std::cout << "\nОшибочный индекс!";
            std::exit(1);
        }
        arr[n] = elvalue;
    }

    // получение значения элемента массива
    int getel(int n) const {
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
        sa1.putel(j, j * 10);
    }
    // показываем элементы
    for (int j = 0; j < LIMIT; j++) {
        int temp = sa1.getel(j);
        std::cout << "Элемент " << j << " равен " << temp << std::endl;
    }
    return 0;
} 
