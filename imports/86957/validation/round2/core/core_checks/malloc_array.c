#include <stdio.h>
#include <stdlib.h>

int main(void) {
    unsigned n;
    printf("Size of array (1..100000)=");
    if (scanf("%u", &n) != 1 || n == 0 || n > 100000) {
        return 1;
    }
    int* block = malloc((size_t)n * sizeof *block);
    if (block == NULL) {
        return 1;
    }
    // Здесь можно работать с n элементами после их инициализации.
    free(block);
    block = NULL;
    return 0;
}
