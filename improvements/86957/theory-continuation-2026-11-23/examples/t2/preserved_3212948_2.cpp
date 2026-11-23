#include <iostream>
#include <limits>
#include <string>

int main() {
    int group{};
    if (!(std::cin >> group)) {
        return 1;
    }
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');

    std::string name;
    if (!std::getline(std::cin, name)) {
        return 1;
    }
    std::cout << group << '\n' << name << '\n';
}
