int main(){
union Ints {
    unsigned short int a;
    unsigned int b;
    unsigned long int c;
};

// указатель на объединение
Ints *p;

// выделить память для объединения
p = new Ints;

// доступ к полям с помощью указателя
p->a = 200;
p->b = 3400;

// После использования освободить объект
delete p;
}