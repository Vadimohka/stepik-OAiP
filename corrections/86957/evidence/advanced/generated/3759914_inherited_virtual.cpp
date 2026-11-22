struct Base { virtual int f() = 0; virtual int g() { return 7; } };
struct Derived : Base { int f() override { return 3; } };
int main(){ Derived d; Base& b = d; return b.f() == 3 && b.g() == 7 ? 0 : 1; }
