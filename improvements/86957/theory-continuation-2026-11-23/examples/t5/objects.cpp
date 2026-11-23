#include <iostream>

class SomeClass {
    int data_{};
public:
    void setdata(int data) { data_ = data; }
    int data() const { return data_; }
};

int main() {
    SomeClass first, second;
    std::cout << first.data() << ' ' << second.data() << '\n';
    first.setdata(1066);
    second.setdata(1776);
    std::cout << first.data() << ' ' << second.data() << '\n';
    return 0;
}
