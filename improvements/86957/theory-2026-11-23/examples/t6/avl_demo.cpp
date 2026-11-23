#include "avl.hpp"
#include <iostream>

int main() {
    avl_example::Tree tree;
    for (int key : {30, 10, 20, 40}) {
        avl_example::insert(tree, key, std::to_string(key));
    }
    avl_example::insert(tree, 20, "replacement");
    std::cout << tree->key << ' ' << tree->height << '\n';
    avl_example::erase(tree, 20);
    for (int key : {10, 20, 30, 40}) {
        if (const auto* node = avl_example::find(tree, key)) {
            std::cout << node->key << ':' << node->value << ' ';
        }
    }
    std::cout << '\n';
}
