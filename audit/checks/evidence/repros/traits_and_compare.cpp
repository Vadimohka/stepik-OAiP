#include <iostream>
#include <cstring>
#include <string>
#include <type_traits>
int main(){int a[4]{};static_assert(std::is_array<decltype(a)>::value,"array");static_assert(!std::is_pointer<decltype(nullptr)>::value,"nullptr_t");static_assert(std::is_same<decltype('a'),char>::value,"char");static_assert(std::is_same<decltype(std::string().c_str()),const char*>::value,"c_str");std::cout<<(std::strcmp("a","b")<0)<<" "<<a[3];}