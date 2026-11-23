#include <iostream>
int main() {
    int first{10}, second{20};
    int* current = &first;
    int** handle = &current;
    **handle = 11;
    *handle = &second;
    **handle = 22;
    std::cout << first << ' ' << second << ' ' << *current << '\n';
}
