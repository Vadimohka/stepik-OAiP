#include <iostream>
#include <type_traits>
int main(){signed char a=105,b=30;static_assert(std::is_same<decltype(a+b),int>::value,"promotion");signed char c=a+b;std::cout<<(a+b)<<" "<<(int)c;}