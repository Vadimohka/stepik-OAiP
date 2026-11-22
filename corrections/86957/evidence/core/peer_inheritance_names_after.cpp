#include <string>
#include <cstdio>

struct price { // описание стоимости
    int val; // стоимость
    char type; // единица измерения
    price(int vx, char v) {
        val = vx, type = v;
    }
};

struct unit : virtual public price { // описание устройства
    std::string name; // наименование
    unit(const char *x, int vx = 0, char v = ' ') : price(vx, v) {
        name = x;
    }

    void print() {
        printf("\nUnit %s %d %c", name.c_str(), val, type);
    }
};

struct box : virtual public price { // описание упаковки
    std::string name; // наименование
    box(const char *x, int vx = 0, char v = ' ') : price(vx, v) {
        name = x;
    }

    void print() {
        printf("\nBox %s %d %c", name.c_str(), val, type);
    }
};

// Описание устройства в упаковке с полной стоимостью
struct unit_box : public unit, public box {
    std::string name; // наименование товара в упаковке
    unit_box(const char *x, int vx, // наименование и цена товара
             const char *y, int vy, // наименование и цена упаковки
             const char *z, // общее наименование товара в упаковке
             char v) : // единица измерения цены
             unit(x), box(y), price(vx + vy, v) {
        name = z;
    }

    void print() {
        printf("\nUNIT_BOX %s,", name.c_str());
        printf("\nBOX %s,\nUNIT %s,", box::name.c_str(), unit::name.c_str());
        printf("\nPRICE %d %d %d %c", box::val, unit::val, val, type);
    }
};


int main() {
    for (int n : {0,19,20,39,40,200}) {
        const std::string first(n,'a'), second(n+1,'b'), total(2*n,'c');
        unit_box item(first.c_str(),4,second.c_str(),6,total.c_str(),'p');
        if(item.unit::name!=first || item.box::name!=second || item.name!=total) return 1;
        price* from_unit=static_cast<unit*>(&item);
        price* from_box=static_cast<box*>(&item);
        if(from_unit!=from_box || from_unit->val!=10 || from_unit->type!='p') return 2;
        auto copy=item;
        copy.name += "changed";
        if(item.name!=total) return 3;
        item.print();
    }
}
