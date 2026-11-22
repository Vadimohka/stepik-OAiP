#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>

int main() {
int values[]{10, 20, 30};
int* p = values;
int b = *p++; // b=10, p указывает на values[1]
b = ++*p;     // values[1]=21, b=21, p не изменился
b = *++p;     // p указывает на values[2], b=30
assert(b==30 && values[1]==21 && p==values+2);
}
