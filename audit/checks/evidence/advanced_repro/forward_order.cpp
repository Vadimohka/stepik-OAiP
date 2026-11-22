#include <iostream>
#include <vector>
#include <utility>
template<typename T>
void foo(T&& arg) {
    bar(std::forward<T>(arg));
}

void bar(std::vector<int>&& v) {
    std::cout << "r-value reference" << std::endl;
}

void bar(std::vector<int>& v) {
    std::cout << "l-value reference" << std::endl;
}

int main() {
    std::vector<int> v1{1, 2, 3};
    foo(v1); // передача l-value
    foo(std::vector<int>{1, 2, 3}); // передача r-value

    return 0;
}