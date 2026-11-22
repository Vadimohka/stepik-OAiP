#include <stdio.h>
#include <stdlib.h>

int main(void) {
    const unsigned maxNumber = 100;
    unsigned size;
    printf("Enter number from 0 to %u: ", maxNumber);
    if (scanf("%u", &size) != 1 || size > maxNumber) {
        return 1;
    }
    if (size == 0) {
        return 0;
    }
    int* p = malloc(size * sizeof *p);
    if (p == NULL) {
        return 1;
    }
    for (unsigned i = 0; i < size; ++i) {
        p[i] = (int)(i * i);
    }
    for (unsigned i = 0; i < size; ++i) {
        printf("%d ", p[i]);
    }
    printf("\n");
    free(p);
    return 0;
}