#include <iostream>
 
int main() {   
    int age{};
    double weight{};
    std::cout << "Input age: ";
    if (!(std::cin >> age >> weight)) return 1;
    std::cout << "Your age: " << age << "\t your weight: " << weight << std::endl;
    return 0;
}
