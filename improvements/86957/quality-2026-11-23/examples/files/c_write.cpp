#include <cstdio>

int main() {
    std::FILE* file = std::fopen("message.txt", "wb");
    if (file == nullptr) {
        std::fputs("Cannot open message.txt\n", stderr);
        return 1;
    }

    const char message[] = "Hello, files!\n";
    const std::size_t size = sizeof message - 1;
    const std::size_t written = std::fwrite(message, 1, size, file);
    const int closed = std::fclose(file);
    if (written != size || closed != 0) {
        std::fputs("Cannot finish message.txt\n", stderr);
        return 2;
    }
}
