#include <iostream>

class Counter {
private:
    unsigned int count;

public:
    Counter() {
        count = 0;
    }

    Counter(int c) {
        count = c;
    }

    unsigned int get_count() {
        return count;
    }

    Counter operator++() {
        ++count;
        return Counter(count);
    }
};

int main() {
    Counter c1, c2; // определяем переменные
    std::cout << "\nc1 = " << c1.get_count(); // выводим на экран
    std::cout << "\nc2 = " << c2.get_count();
    ++c1; // увеличиваем c1
    c2 = ++c1; // c1 = 2, c2 = 2
    std::cout << "\nc1 = " << c1.get_count(); // снова показываем значения
    std::cout << "\nc2 = " << c2.get_count() << std::endl;
    return 0;
} 
