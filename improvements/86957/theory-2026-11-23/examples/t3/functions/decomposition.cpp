#include <iostream>

int maximum_of_two(int a, int b) {
    if (a > b) {
        return a;
    }
    return b;
}

int maximum_of_three(int a, int b, int c) {
    return maximum_of_two(maximum_of_two(a, b), c);
}

int main() {
    int a = 0;
    int b = 0;
    int c = 0;
    if (!(std::cin >> a >> b >> c)) {
        std::cerr << "input error\n";
        return 1;
    }
    std::cout << maximum_of_three(a, b, c) << '\n';
    return 0;
}
