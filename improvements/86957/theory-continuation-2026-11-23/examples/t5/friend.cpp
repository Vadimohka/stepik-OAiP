#include <iostream>

class Value {
    int number_;
public:
    explicit Value(int number) : number_(number) {}
    friend bool equal(const Value& left, const Value& right);
};

bool equal(const Value& left, const Value& right) {
    return left.number_ == right.number_;
}

int main() {
    const Value first{7}, second{7}, third{8};
    std::cout << std::boolalpha << equal(first, second) << ' '
              << equal(first, third) << '\n';
    return 0;
}
