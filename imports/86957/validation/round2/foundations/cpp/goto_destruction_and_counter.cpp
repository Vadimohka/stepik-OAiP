#include <cassert>
int destroyed=0;
struct Guard { ~Guard() { ++destroyed; } };
int main() {
    { Guard guard; goto after; }
after:
    assert(destroyed==1);
    int x=1;
loop1:
    x++;
    if (x<=100) goto loop1;
    assert(x==101);
}
