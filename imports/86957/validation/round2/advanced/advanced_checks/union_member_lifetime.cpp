#include <cassert>
// объединение целочисленных типов
union Ints {
    unsigned short int a;
    unsigned int b;
    unsigned long int c;
};

// структура, содержащая 2 строки
struct ArrayOfChars {
    char A[10];
    char B[8];
};

// объявление типа "объединение Floats"
union Floats {
    float f; // рассматривается 4 байта
    double d; // рассматривается 8 байт
};
class MyPoint {
    public:
        int x;
        int y;

        // методы класса
        int GetX(void) { return x; }
        int GetY(void) { return y; }
        void SetXY(int nx, int ny) { x = nx; y = ny; }
};
union Types {
    Floats Fl; // объединение
    Ints I;   // объединение
    ArrayOfChars A; // структура
    MyPoint MP;   // класс
};
int main(){
// объявить переменную типа "объединение Types"
Types T;

// изменить значения полей переменной T
T.Fl.f = (float)20.35; // объединение Floats
T.I.b = 230; // объединение Ints
T.A.A[2] = 'A'; // структура ArrayOfChars
T.MP = MyPoint{}; // тривиальное присваивание начинает время жизни поля MP
T.MP.SetXY(3,8); // теперь метод вызывается у активного члена union
int d;
d = T.MP.GetX(); // d = 3
assert(d==3 && T.MP.GetY()==8);
}
