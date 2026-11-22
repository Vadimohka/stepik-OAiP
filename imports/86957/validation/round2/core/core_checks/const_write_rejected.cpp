#include <iostream>

void foo(const int* ptr)
{
*ptr = 100;
}

int main(void)
{
int x = 200;
int* ptr = &x;
std::cout << "Before x = " << x << ";" << "\t";
foo(ptr);
std::cout << "After x = " << x << std::endl;
return 0;
}
