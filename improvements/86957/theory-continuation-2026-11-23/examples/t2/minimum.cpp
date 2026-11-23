#include <iostream>
int minimum(int a, int b) {
    if (a < b) {
        return a;
    }
    return b;
}
int main() {
    std::cout << minimum(4, 7) << ' ' << minimum(7, 4)
              << ' ' << minimum(4, 4) << '\n';
    return 0;
}
