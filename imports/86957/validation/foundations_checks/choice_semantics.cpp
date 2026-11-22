#include <climits>
#include <iostream>
static_assert(CHAR_BIT == 8);
static_assert(static_cast<signed char>(256L) == 0);
static_assert(static_cast<signed char>(0b11111111) == -1);
static_assert(double(3/2) == 1.0);
static_assert((double)(int)(double)3/2 == 1.5);
static_assert('1' == 49); // the quiz explicitly assumes ASCII-compatible encoding
static_assert('1' - 49 == 0);
static_assert(1 + true == 2);
static_assert(1 + bool(255) == 2);
int main() {
    unsigned char a=255; ++a;
    if(a != 0) return 1;
    int x=3; int p=++x;
    if(p != 4 || x != 4) return 2;
    x=3; int q=x++;
    if(q != 3 || x != 4) return 3;
    int z=1; switch(z) case 1: ++z; switch(z);
    return 0;
}