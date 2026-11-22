#include <stdio.h>
 
struct Point {
    int x;
    int y;
};
 
struct Apex {
    int a;
    int b;
};

int main() {
    struct Point point = {10, 20};
    struct Apex apex;
 
    apex.a = point.x;
    apex.b = point.y;
 
    printf("a = %d, b = %d", apex.a, apex.b);

}
