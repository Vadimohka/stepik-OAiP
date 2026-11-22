#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>

int main() {
signed char a = 105;
signed char b = 30;
int sum = a + b;                         // 135
signed char narrowed = static_cast<signed char>(sum); // -121: C++20, 8 бит
static_assert(CHAR_BIT==8);static_assert(std::is_same_v<decltype(a+b),int>);assert(sum==135 && narrowed==-121);
}
