#include <iostream>
 
int main() {
    int a = 10;
    const int *pa = &a;
    std::cout <<"value=" << *pa << std::endl;     // 10
    a = 22;
    std::cout <<"value=" << *pa << std::endl;     // 22
    //*pa = 34;     // так делать нельзя
     
    return 0;
}