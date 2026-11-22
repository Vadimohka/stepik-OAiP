#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>

int main() {
int var = 10;
int* ptr = &var;
*ptr = 20;       // var теперь равен 20
int** pptr = &ptr;
**pptr = 30;     // var теперь равен 30
assert(var==30);
}
