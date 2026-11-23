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
    Model model{10, {1, "Acura"}, "CL", 2003};
    Make* make = &model.make;
    int* id = &model.id;
    *id = 11;
    std::cout << make->name << ' ' << model.id << '\n';
    const Model& view = model;
    const Make* read_only = &view.make;
    std::cout << read_only->id << '\n';
    return 0;
}
