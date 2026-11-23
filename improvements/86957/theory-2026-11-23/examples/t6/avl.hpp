#pragma once
#include <algorithm>
#include <memory>
#include <string>
#include <utility>

namespace avl_example {
struct Node {
    int key;
    std::string value;
    std::unique_ptr<Node> left, right;
    int height = 1;
    Node(int k, std::string v) : key(k), value(std::move(v)) {}
};
using Tree = std::unique_ptr<Node>;

inline int height(const Tree& tree) {
    return tree ? tree->height : 0;
}
inline void update(Node& node) {
    node.height = 1 + std::max(height(node.left), height(node.right));
}
inline int balance(const Tree& tree) {
    return tree ? height(tree->left) - height(tree->right) : 0;
}

// Preconditions: tree and tree->right exist.
inline void rotate_left(Tree& tree) {
    Tree new_root = std::move(tree->right);
    tree->right = std::move(new_root->left);
    update(*tree);
    new_root->left = std::move(tree);
    update(*new_root);
    tree = std::move(new_root);
}
// Preconditions: tree and tree->left exist.
inline void rotate_right(Tree& tree) {
    Tree new_root = std::move(tree->left);
    tree->left = std::move(new_root->right);
    update(*tree);
    new_root->right = std::move(tree);
    update(*new_root);
    tree = std::move(new_root);
}

// The children are AVL trees, and the height changed by at most one.
inline void rebalance(Tree& tree) {
    if (!tree) return;
    update(*tree);
    if (balance(tree) > 1) {
        if (balance(tree->left) < 0) rotate_left(tree->left);
        rotate_right(tree);
    } else if (balance(tree) < -1) {
        if (balance(tree->right) > 0) rotate_right(tree->right);
        rotate_left(tree);
    }
}

// A duplicate key preserves the existing value and returns false.
inline bool insert(Tree& tree, int key, const std::string& value) {
    if (!tree) {
        tree = std::make_unique<Node>(key, value);
        return true;
    }
    bool inserted = false;
    if (key < tree->key) inserted = insert(tree->left, key, value);
    else if (key > tree->key) inserted = insert(tree->right, key, value);
    else return false;
    rebalance(tree);
    return inserted;
}

inline const Node* find(const Tree& tree, int key) {
    const Node* node = tree.get(); // Non-owning observer.
    while (node) {
        if (key < node->key) node = node->left.get();
        else if (key > node->key) node = node->right.get();
        else return node;
    }
    return nullptr;
}

inline bool erase(Tree& tree, int key) {
    if (!tree) return false;
    bool removed = false;
    if (key < tree->key) removed = erase(tree->left, key);
    else if (key > tree->key) removed = erase(tree->right, key);
    else {
        removed = true;
        if (!tree->left) {
            Tree old_root = std::move(tree);
            tree = std::move(old_root->right);
        } else if (!tree->right) {
            Tree old_root = std::move(tree);
            tree = std::move(old_root->left);
        } else {
            const Node* successor = tree->right.get();
            while (successor->left) successor = successor->left.get();
            // Copy the potentially throwing value before changing the key.
            std::string replacement = successor->value;
            tree->key = successor->key;
            tree->value = std::move(replacement);
            erase(tree->right, tree->key);
        }
    }
    rebalance(tree);
    return removed;
}
} // namespace avl_example
