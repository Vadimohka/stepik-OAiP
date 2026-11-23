#include <iostream>

class Storage;

class Display {
public:
    void show(const Storage& storage) const;
};

class Storage {
    int integer_;
    double real_;
public:
    Storage(int integer, double real) : integer_(integer), real_(real) {}
    friend void Display::show(const Storage& storage) const;
};

void Display::show(const Storage& storage) const {
    std::cout << storage.integer_ << ' ' << storage.real_ << '\n';
}

int main() {
    const Storage storage{5, 6.5};
    const Display display;
    display.show(storage);
    return 0;
}
