#include <stdlib.h>
int main(void) {
size_t n = 10, new_n = 20;
int* block = malloc(n * sizeof *block);
int* zeroed = calloc(n, sizeof *zeroed);
if (block == NULL || zeroed == NULL) {
    free(block);
    free(zeroed);
    return 1;
}
int* replacement = realloc(block, new_n * sizeof *block);
if (replacement != NULL) {
    block = replacement;
}
// При отказе realloc блок block по-прежнему принадлежит нам.
free(block);
free(zeroed);
return 0;
}
