#include <type_traits>
template<class T>T copy_object(T& obj) noexcept(std::is_pod<T>){return obj;}
int main(){int i=1;copy_object(i);}