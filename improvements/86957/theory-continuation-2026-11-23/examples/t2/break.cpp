#include <iostream>
int main() {
    for (int i = 0; i < 10; ++i) {
        if (i == 3) {
            break;
        }
        std::cout << i << '\n';
    }
    std::cout << "done\n";
}
