#include <iostream>
 
int main() {   
    int age{};
    double weight{};
    std::cout << "Input age: ";
    if (!(std::cin >> age)) return 1;
    std::cout << "Input weight: ";
    if (!(std::cin >> weight)) return 1;
    std::cout << "Your age: " << age << "\t your weight: " << weight << std::endl;
    return 0;
}
