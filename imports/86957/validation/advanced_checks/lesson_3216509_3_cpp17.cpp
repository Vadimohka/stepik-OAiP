#include <cstdio>
#include <cstring>

struct point {
    unsigned int x : 5;
    unsigned int y : 3;
};

int main() {
    point center = {2, 5};
    unsigned char first_byte{};
    std::memcpy(&first_byte, &center, sizeof first_byte);
    for (int bit = 7; bit >= 0; --bit) {
        std::printf("%u ", (static_cast<unsigned>(first_byte) >> bit) & 1u);
    }
    std::printf("\nsizeof(point) = %zu\n", sizeof(point));
}
