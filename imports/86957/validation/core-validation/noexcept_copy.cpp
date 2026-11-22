#include <type_traits>

template <typename T>
T copy_object(const T& obj) noexcept(std::is_nothrow_copy_constructible<T>::value) {
    return obj;
}
#include <cassert>
struct MayThrow { MayThrow(const MayThrow&) noexcept(false) {} };
int main(){int n=42;static_assert(noexcept(copy_object(n)));static_assert(!std::is_nothrow_copy_constructible<MayThrow>::value);assert(copy_object(n)==42);}
