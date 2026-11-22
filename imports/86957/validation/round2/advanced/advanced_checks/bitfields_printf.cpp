#include <stdio.h>
 
struct point {
    unsigned int x:5;   // 0-31
    unsigned int y:3;   // 0-7
};
 
int main(void) {
    struct point center = {0, 5};
    center.x = 2;
    printf("x = %u    y = %u\n", (unsigned)center.x, (unsigned)center.y);  // x = 2  y = 5
     
    return 0;
}