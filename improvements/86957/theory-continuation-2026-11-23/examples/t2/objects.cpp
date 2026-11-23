#include <iostream>
int main() {
    int age{28};
    int copy = age;
    age = 29;
    const int limit{100};
    int zero{};
    std::cout << age << ' ' << copy << ' ' << limit << ' ' << zero << '\n';
}
