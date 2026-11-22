#include <stdlib.h>

int main(void) {
    const size_t rowNum = 10, colNum = 10;
    float** p = malloc(rowNum * sizeof *p);
    if (p == NULL) {
        return 1;
    }
    for (size_t i = 0; i < rowNum; ++i) {
        p[i] = malloc(colNum * sizeof *p[i]);
        if (p[i] == NULL) {
            while (i > 0) {
                free(p[--i]);
            }
            free(p);
            return 1;
        }
    }
    // Здесь можно работать с таблицей после инициализации элементов.
    for (size_t i = 0; i < rowNum; ++i) {
        free(p[i]);
    }
    free(p);
    return 0;
}
