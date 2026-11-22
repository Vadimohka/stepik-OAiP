#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    size_t capacity = 10;
    size_t count = 0;
    char** words = malloc(capacity * sizeof *words);
    char buffer[128];
    int failed = 0;
    if (words == NULL) {
        return 1;
    }
    while (scanf("%127s", buffer) == 1 && strcmp(buffer, "end") != 0) {
        if (count == capacity) {
            if (capacity > SIZE_MAX / sizeof *words - 10) {
                failed = 1;
                break;
            }
            size_t new_capacity = capacity + 10;
            char** replacement = realloc(words, new_capacity * sizeof *words);
            if (replacement == NULL) {
                failed = 1;
                break;
            }
            words = replacement;
            capacity = new_capacity;
        }
        words[count] = malloc(strlen(buffer) + 1);
        if (words[count] == NULL) {
            failed = 1;
            break;
        }
        strcpy(words[count], buffer);
        ++count;
    }
    for (size_t i = 0; i < count; ++i) {
        puts(words[i]);
        free(words[i]);
    }
    free(words);
    if (failed) {
        fputs("Cannot allocate memory\n", stderr);
        return 1;
    }
    return 0;
}
