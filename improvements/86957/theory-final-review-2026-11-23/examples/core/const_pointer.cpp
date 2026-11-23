#include <iostream>
 
int main() {
    int a = 10;
    int *const pa = &a;
    std::cout << "value=" << *pa << std::endl;      // 10
    *pa = 22;                                       // меняем значение
    std::cout << "value=" << *pa << std::endl;      // 22
  
    int b = 45;
    // pa = &b;         так нельзя сделать
     
    return 0;
}