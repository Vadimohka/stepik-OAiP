#include "rbt.hpp"
#include <iostream>
#include <string>

int main() {
    RBT<int, std::string> tree;
    for (int key : {10, 20, 30}) tree.add(key, std::to_string(key));
    tree.add(20, "duplicate");
    std::cout << tree.findValueWithKey(20) << '\n';
    tree.remove(10);
    tree.remove(20);
    std::cout << std::boolalpha << tree.contains(10) << ' '
              << tree.contains(20) << ' ' << tree.contains(30) << '\n';
}
