#include <stdio.h>
 
struct Test1 {
    char a;
    char b;
    int c;
} A;
 
struct Test2 {
    int x;
    int y;
} B;
 
struct Test3 {
    char a;
    char b;
    char c;
    int d;
} C;
 
int main() {
    printf("sizeof(A) = %zu\n", sizeof(A));
    printf("sizeof(B) = %zu\n", sizeof(B));
    printf("sizeof(C) = %zu\n", sizeof(C));

}