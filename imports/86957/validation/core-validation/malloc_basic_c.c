#include <stdlib.h>

int main(void) {
    int* p = malloc(100);
    if (p == NULL) {
        return 1;
    }
    free(p);
    return 0;
}