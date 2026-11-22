#include <iostream>
#include <clocale>

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
    void showdist() const {
        std::cout << feet << " футов " << inches << " дюймов";
    }
 
    // сложение
    Distance add_dist(const Distance&) const; 

    // деструктор класса Distance
    ~Distance() { }
};

// сложение данного объекта с d2, возврат суммы
Distance Distance::add_dist(const Distance& d2) const {
    Distance temp; // временная переменная
    // feet = 0; // Ошибка: нельзя изменить поле
    // d2.feet = 0; // Ошибка: нельзя изменить d2
    temp.inches = inches + d2.inches; // сложение дюймов

    // если сумма превышает 12.0, то уменьшаем ее на 12.0
    // и увеличиваем число футов на 1
    if(temp.inches >= 12.0) {
        temp.inches -= 12.0;
        temp.feet = 1;
    }
    temp.feet += feet + d2.feet; // сложение футов
    return temp;
}

int main() {
    setlocale(LC_ALL, "Russian");
    Distance dist1, dist3; // две длины
    Distance dist2(11, 6.25); // определение и инициализация dist2
    dist1.getdist(); // ввод dist1
    dist3 = dist1.add_dist(dist2); //dist3 = dist1 + dist2

    // вывод всех длин
    std::cout << "\ndist1 = ";
    dist1.showdist();
    std::cout << "\ndist2 = ";
    dist2.showdist();
    std::cout << "\ndist3 = ";
    dist3.showdist();
    std::cout << std::endl;
    return 0;
} 
