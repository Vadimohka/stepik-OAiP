#include <iostream>

int next_local() {
    int counter = 0;
    return ++counter;
}

// Demonstration: called twice; the counter must not overflow int.
int next_static() {
    static int counter = 0;
    return ++counter;
}

int main() {
    const int local_first = next_local();
    const int local_second = next_local();
    const int static_first = next_static();
    const int static_second = next_static();
    std::cout << local_first << ' ' << local_second << '\n';
    std::cout << static_first << ' ' << static_second << '\n';
    return 0;
}
