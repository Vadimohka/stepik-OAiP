#include <iostream>

// длина в английской системе
class Distance { 
private:
    int feet;
    float inches;

public: 
    // конструктор без аргументов
    Distance() {
        feet = 0;
        inches = 0;
    }

    // конструктор с двумя аргументами
    Distance(int ft, float in) {
        feet = ft;
        inches = in;   
    }

    // ввод длины пользователем
    void getdist() {
        std::cout << "Введите число футов: ";
        std::cin >> feet;
        std::cout << "Введите число дюймов: "; 
        std::cin >> inches;
    }

    // вывод полей на экран
    void showdist() {
        std::cout << feet << " футов " << inches << " дюймов";
    }
};
int main() {
    setlocale(LC_ALL, "Russian");
    Distance dist1; // первая длина
    Distance dist2(11, 6.25); // определение и инициализация
    dist1.getdist(); // ввод dist1

    // вывод всех длин
    std::cout << "\ndist1 = ";
    dist1.showdist();
    std::cout << "\ndist2 = ";
    dist2.showdist();
    std::cout << std::endl;
    return 0;
} 
