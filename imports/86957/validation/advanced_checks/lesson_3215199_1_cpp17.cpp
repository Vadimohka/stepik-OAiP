#include <stdio.h>

int main(void) {
    FILE* file = fopen("ttt.txt", "wb");
    if (file == NULL) {
        return 1;
    }
    const char message[] = "Hello, world!";
    size_t written = fwrite(message, 1, sizeof message - 1, file);
    int close_result = fclose(file);
    return written == sizeof message - 1 && close_result == 0 ? 0 : 1;
}
