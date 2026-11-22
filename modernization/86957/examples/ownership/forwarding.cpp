#include <iostream>
#include <utility>
#include <vector>

void inspect(const std::vector<int>& values) {
    std::cout << "const lvalue reference: " << values.size() << '\n';
}

void inspect(std::vector<int>&& values) {
    std::cout << "rvalue reference: " << values.size() << '\n';
}

template<class T>
void relay(T&& argument) {
    inspect(std::forward<T>(argument));
}

int main() {
    std::vector<int> values{1, 2, 3};
    relay(values);
    relay(std::vector<int>{4, 5});
    relay(std::move(values));
    std::cout << "still present: " << values.size() << '\n';
}
