#include <iostream>

// длина в английской системе
class Distance {
private:
    int feet;
    float inches;

public:
    // конструктор с двумя аргументами
    Distance(int ft, float in) {
        feet = ft;
        inches = in;
    }

    // неконстантный метод
    void getdist() {
        std::cout << "Введите число футов: ";
        std::cin >> feet;
        std::cout << "Введите число дюймов: ";
        std::cin >> inches;
    }

    // константный метод
    void showdist() const {
        std::cout << feet << " футов " << inches << " дюймов";
    }

int main() {
    setlocale(LC_ALL, "Russian");
    const Distance football(300, 0);
    // football.getdist(); // ошибка: метод getdist() неконстантный
    std::cout << "Длина поля равна ";
    football.showdist(); // корректно
    std::cout << std::endl;
    return 0;
}