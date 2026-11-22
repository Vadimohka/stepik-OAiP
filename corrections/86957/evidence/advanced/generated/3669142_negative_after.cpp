#include <iostream>
class Display; // Предварительное объявление для класса Display
 
class Storage {
private:
    int m_nValue;
    double m_dValue;

public:
    Storage(int nValue, double dValue) {
        m_nValue = nValue;
        m_dValue = dValue;
    }
 
    // Сделаем функцию-член Display::displayItem другом класса Storage
    friend void Display::displayItem(const Storage& storage); 
    // Ошибка: Storage не увидел полное определение класса Display
};

class Display {
private:
    bool m_displayIntFirst;

public:
    Display(bool displayIntFirst) {
        m_displayIntFirst = displayIntFirst;
    }
 
    void displayItem(const Storage &storage) {
        if (m_displayIntFirst)
            std::cout << storage.m_nValue << ' ' << storage.m_dValue << '\n';
        else  // Сначала отображаем double
            std::cout << storage.m_dValue << ' ' << storage.m_nValue << '\n';
    }
};