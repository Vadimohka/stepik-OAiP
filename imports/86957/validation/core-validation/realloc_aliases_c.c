#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int* p1 = malloc(10 * sizeof *p1);
    if (p1 == NULL) {
        return 1;
    }
    for (int i = 0; i < 10; ++i) {
        p1[i] = i;
    }
    int* p2 = p1;
    int* replacement = realloc(p1, 20 * sizeof *p1);
    if (replacement == NULL) {
        free(p1);
        return 1;
    }
    p1 = replacement;
    p2 = p1; // Обновляем алиас после успешного realloc.
    for (int i = 0; i < 10; ++i) {
        printf("%d ", p2[i]);
    }
    free(p1);
    p1 = NULL;
    p2 = NULL;
    return 0;
}