#include <cstring>
#include <cstdio>

struct price { // описание стоимости
    int val; // стоимость
    char type; // единица измерения
    price(int vx, char v) {
        val = vx, type = v;
    }
};

struct unit : virtual public price { // описание устройства
    char name[20]; // наименование
    unit(const char *x, int vx = 0, char v = ' ') : price(vx, v) {
        strcpy(name, x);
    }

    void print() {
        printf("\nUnit %s %d %c", name, val, type);
    }
};

struct box : virtual public price { // описание упаковки
    char name[20]; // наименование
    box(const char *x, int vx = 0, char v = ' ') : price(vx, v) {
        strcpy(name, x);
    }

    void print() {
        printf("\nBox %s %d %c", name, val, type);
    }
};

// Описание устройства в упаковке с полной стоимостью
struct unit_box : public unit, public box {
    char name[40]; // наименование товара в упаковке
    unit_box(const char *x, int vx, // наименование и цена товара
             const char *y, int vy, // наименование и цена упаковки
             const char *z, // общее наименование товара в упаковке
             char v) : // единица измерения цены
             unit(x), box(y), price(vx + vy, v) {
        strcpy(name, z);
    }

    void print() {
        printf("\nUNIT_BOX %s,", name);
        printf("\nBOX %s,\nUNIT %s,", box::name, unit::name);
        printf("\nPRICE %d %d %d %c", box::val, unit::val, val, type);
    }
};

int main() {
    unit_box tv_set("телевизор", 1000, "упаковка", 10, "телевизор в упаковке", 'p');
    tv_set.print();
    box b("b-111", 111, '$');
    unit u("u-222", 222, 'Y');
    b.print();
    u.print();
}
