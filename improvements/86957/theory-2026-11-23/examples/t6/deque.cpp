#include <deque>
#include <iostream>

int main() {
    std::deque<int> values{20, 30};
    int& first = values.front();
    values.push_front(10);
    values.push_back(40);
    std::cout << first << ' ' << values.at(2) << '\n';
    // References survive insertion at the ends; old iterators do not.
    for (auto it = values.begin(); it != values.end(); ++it) {
        std::cout << *it << ' ';
    }
    std::cout << '\n';
}
