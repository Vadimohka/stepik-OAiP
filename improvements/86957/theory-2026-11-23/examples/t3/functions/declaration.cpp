#include <iostream>

int minimum(int left, int right);

int main() {
    int a = 0;
    int b = 0;
    if (!(std::cin >> a >> b)) {
        std::cerr << "input error\n";
        return 1;
    }
    std::cout << minimum(a, b) << '\n';
    return 0;
}

int minimum(int left, int right) {
    if (left < right) {
        return left;
    }
    return right;
}
