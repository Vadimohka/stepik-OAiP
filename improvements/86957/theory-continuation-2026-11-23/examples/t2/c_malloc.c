#include <stdio.h>
#include <stdlib.h>

int main(void) {
    const size_t count = 4;
    int* values = malloc(count * sizeof *values);
    if (values == NULL) {
        fputs("MEMORY\n", stderr);
        return 1;
    }
    for (size_t i = 0; i < count; ++i) {
        values[i] = (int)(i * i);
    }
    for (size_t i = 0; i < count; ++i) {
        printf("%d%c", values[i], i + 1 == count ? '\n' : ' ');
    }
    free(values);
    values = NULL;
    return 0;
}
