#include <iostream>
 
int main() {
    const int a = 10;
    const int *pa = &a;
    std::cout << "address=" << pa << "\tvalue=" << *pa << std::endl;
     
    return 0;
}