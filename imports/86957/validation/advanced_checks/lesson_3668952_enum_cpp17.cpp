class date {
    // описание собственных типов класса
    // по умолчанию атрибут доступа private
    enum date_month { January = 1, February, March, April, May, June, July, August, September, October, November, December };

    // Декларация элементов данных класса
    int day, month, year; // private

// изменение атрибута доступа
public: 
    // Описание функций-элементов
    void set(int, int, int); // public
    void next(); // public

protected: // изменение атрибута доступа
    void print(); // protected
};

int main() {}
