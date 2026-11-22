#include <iostream>

class foo {
private:
    // общее поле для всех объектов в смысле "объявления"
    static int count; 

public:
    // инкрементирование при создании объекта
    foo() {
        count++;
    }

    // возвращает значение count
    int getcount() {
        return count;
    }
};

int foo::count = 0; // *определение* count

int main() {
    foo f1, f2, f3; // создание трех объектов
    // каждый объект видит одно и то же значение
    std::cout << "Число объектов: " << f1.getcount() << std::endl;
    std::cout << "Число объектов: " << f2.getcount() << std::endl;
    std::cout << "Число объектов: " << f3.getcount() << std::endl;
    return 0;
}
