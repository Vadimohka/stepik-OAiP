#include <array>
#include <iostream>
#include <string>

struct Person {
    std::string name;
    int age{};
};

int main() {
    std::array<Person, 2> people{{{"Anna", 20}, {"Boris", 19}}};
    Person* selected = &people[1];
    selected->age = 21;
    const Person* reader = selected;
    std::cout << reader->name << ' ' << reader->age << '\n';
    std::cout << people[0].age << '\n';
    return 0;
}
