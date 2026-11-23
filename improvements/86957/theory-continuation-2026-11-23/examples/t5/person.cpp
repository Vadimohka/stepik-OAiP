#include <iostream>
#include <string>

struct Person {
    std::string name;
    int age{};
};

int main() {
    Person tom{"Tom", 34};
    Person unknown{};
    std::cout << tom.name << ' ' << tom.age << '\n';
    std::cout << '"' << unknown.name << "\" " << unknown.age << '\n';
    return 0;
}
