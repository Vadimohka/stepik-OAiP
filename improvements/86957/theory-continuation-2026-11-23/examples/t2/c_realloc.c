#include <stdio.h>
#include <stdlib.h>

int main(void) {
    const size_t old_count = 3;
    const size_t new_count = 5;
    int* values = calloc(old_count, sizeof *values);
    if (values == NULL) {
        fputs("MEMORY\n", stderr);
        return 1;
    }
    for (size_t i = 0; i < old_count; ++i) {
        values[i] = (int)((i + 1) * 10);
    }
    int* replacement = realloc(values, new_count * sizeof *values);
    if (replacement == NULL) {
        free(values);
        fputs("MEMORY\n", stderr);
        return 1;
    }
    values = replacement;
    for (size_t i = old_count; i < new_count; ++i) {
        values[i] = (int)((i + 1) * 10);
    }
    for (size_t i = 0; i < new_count; ++i) {
        printf("%d%c", values[i], i + 1 == new_count ? '\n' : ' ');
    }
    free(values);
    return 0;
}
