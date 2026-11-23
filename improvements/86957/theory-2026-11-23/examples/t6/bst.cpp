#include <iostream>
#include <memory>
#include <string>
#include <utility>

struct BstNode {
    int key;
    std::string value;
    std::unique_ptr<BstNode> left, right;
    BstNode(int k, std::string v) : key(k), value(std::move(v)) {}
};

bool insert_bst(std::unique_ptr<BstNode>& root, int key, const std::string& value) {
    if (!root) {
        root = std::make_unique<BstNode>(key, value);
        return true;
    }
    if (key < root->key) return insert_bst(root->left, key, value);
    if (key > root->key) return insert_bst(root->right, key, value);
    return false; // Preserve the existing value for a duplicate key.
}

int main() {
    std::unique_ptr<BstNode> root;
    insert_bst(root, 20, "root");
    insert_bst(root, 10, "left");
    insert_bst(root, 30, "right");
    const bool inserted = insert_bst(root, 20, "other");
    std::cout << std::boolalpha << inserted << ' ' << root->value << '\n';
    std::cout << root->left->key << ' ' << root->key << ' ' << root->right->key << '\n';
}
