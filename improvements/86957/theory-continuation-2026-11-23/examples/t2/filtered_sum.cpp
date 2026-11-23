#include <iostream>
int main() {
    int sum{};
    int count{};
    for (int i = 1; i <= 100; ++i) {
        if (i % 2 == 0 || i % 3 == 0) {
            continue;
        }
        sum += i;
        ++count;
    }
    std::cout << count << ' ' << sum << '\n';
}
