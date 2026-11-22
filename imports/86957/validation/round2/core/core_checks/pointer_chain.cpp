#include <iostream>

int main() {
    int var = 123; // инициализация переменной var числом 123
    int* ptrvar = &var; // указатель на переменную var
    int** ptr_ptrvar = &ptrvar; // указатель на указатель на переменную var
    int*** ptr_ptr_ptrvar = &ptr_ptrvar;
    std::cout << " var\t\t= " << var << std::endl;
    std::cout << " *ptrvar\t= " << *ptrvar << std::endl;
    std::cout << " **ptr_ptrvar   = " << **ptr_ptrvar << std::endl; // два раза разыменовываем указатель, так как он второго порядка
    std::cout << " ***ptr_ptr_ptrvar = " << ***ptr_ptr_ptrvar << std::endl; // указатель третьего порядка
    std::cout << "\n ***ptr_ptr_ptrvar -> **ptr_ptrvar -> *ptrvar ->      var -> " << var << std::endl;
    std::cout << "\t  " << &ptr_ptr_ptrvar << " -> " << "    " << &ptr_ptrvar << " ->" << &ptrvar << " -> " << &var << " -> " << var << std::endl;
    return 0;
}
