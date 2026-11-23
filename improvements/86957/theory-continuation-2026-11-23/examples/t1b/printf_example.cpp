#include <cstdio>
#include <cstdlib>

int main() {
    if (std::printf("%d %.1f\n", 42, 3.5) < 0) {
        return EXIT_FAILURE;
    }
}
