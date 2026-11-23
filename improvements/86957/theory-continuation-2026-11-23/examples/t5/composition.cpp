#include <iostream>
#include <string>

struct Make {
    int id{};
    std::string name;
};
struct Model {
    int id{};
    Make make;
    std::string name;
    int year{};
};

int main() {
    Model original{10, {1, "Acura"}, "CL", 2003};
    Model copy = original;
    copy.name = "TSX";
    std::cout << original.make.name << ' ' << original.name << ' '
              << original.year << '\n';
    std::cout << copy.name << '\n';
    return 0;
}
