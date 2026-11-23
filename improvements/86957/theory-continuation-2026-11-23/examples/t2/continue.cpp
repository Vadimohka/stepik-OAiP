#include <iostream>
int main() {
    for (int i = 1; i <= 5; ++i) {
        if (i % 2 == 0) {
            continue;
        }
        std::cout << i << '\n';
    }
}
