// Author-side checks of the explanatory implementations; not a student task.
#include "avl.hpp"
#include "rbt.hpp"
#include "hash_table.hpp"
#include <algorithm>
#include <cassert>
#include <climits>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <map>
#include <random>
#include <set>
#include <vector>

std::size_t checked_states = 0;

int check_avl_node(const avl_example::Tree& tree,
                   std::int64_t low, std::int64_t high,
                   const std::map<int, std::string>& expected,
                   std::set<int>& found) {
    if (!tree) return 0;
    assert(low < tree->key && tree->key < high);
    assert(found.insert(tree->key).second);
    const auto item = expected.find(tree->key);
    assert(item != expected.end() && item->second == tree->value);
    const int left = check_avl_node(tree->left, low, tree->key, expected, found);
    const int right = check_avl_node(tree->right, tree->key, high, expected, found);
    assert(std::abs(left - right) <= 1);
    assert(tree->height == 1 + std::max(left, right));
    return tree->height;
}

class CheckedRb : public RBT<int, std::string> {
    int check_node(const std::shared_ptr<Node>& node, const Node* parent,
                   std::int64_t low, std::int64_t high,
                   const std::map<int, std::string>& expected,
                   std::set<int>& found) const {
        if (!node) return 1; // NIL contributes one black node in this checker.
        assert(low < node->key && node->key < high);
        assert(found.insert(node->key).second);
        assert(node->parent.lock().get() == parent);
        const auto item = expected.find(node->key);
        assert(item != expected.end() && item->second == node->data);
        if (!node->color) {
            assert(!node->left || node->left->color);
            assert(!node->right || node->right->color);
        }
        const int left = check_node(node->left, node.get(), low, node->key, expected, found);
        const int right = check_node(node->right, node.get(), node->key, high, expected, found);
        assert(left == right);
        return left + (node->color ? 1 : 0);
    }
public:
    void validate(const std::map<int, std::string>& expected) const {
        assert(!root || (root->color && root->parent.expired()));
        std::set<int> found;
        check_node(root, nullptr, static_cast<std::int64_t>(INT_MIN) - 1,
                   static_cast<std::int64_t>(INT_MAX) + 1, expected, found);
        assert(found.size() == expected.size());
    }
};

void validate(const avl_example::Tree& tree, const CheckedRb& rb,
              const std::map<int, std::string>& expected) {
    std::set<int> found;
    check_avl_node(tree, static_cast<std::int64_t>(INT_MIN) - 1,
                   static_cast<std::int64_t>(INT_MAX) + 1, expected, found);
    assert(found.size() == expected.size());
    rb.validate(expected);
    for (const auto& item : expected) {
        const auto* actual = avl_example::find(tree, item.first);
        assert(actual && actual->value == item.second);
    }
    ++checked_states;
}

void check_tree_sequences() {
    std::vector<int> insertion{0, 1, 2, 3};
    do {
        std::vector<int> removal{0, 1, 2, 3};
        do {
            avl_example::Tree avl;
            CheckedRb rb;
            std::map<int, std::string> expected;
            validate(avl, rb, expected);
            for (int key : insertion) {
                const auto value = std::to_string(key);
                assert(avl_example::insert(avl, key, value));
                rb.add(key, value);
                expected.emplace(key, value);
                validate(avl, rb, expected);
                assert(!avl_example::insert(avl, key, "duplicate"));
                rb.add(key, "duplicate");
                validate(avl, rb, expected);
            }
            for (int key : removal) {
                assert(avl_example::erase(avl, key));
                rb.remove(key);
                expected.erase(key);
                validate(avl, rb, expected);
                assert(!avl_example::erase(avl, key));
                rb.remove(key);
                validate(avl, rb, expected);
            }
        } while (std::next_permutation(removal.begin(), removal.end()));
    } while (std::next_permutation(insertion.begin(), insertion.end()));

    avl_example::Tree avl;
    CheckedRb rb;
    std::map<int, std::string> expected;
    std::mt19937 rng(86957);
    for (int i = 0; i < 6000; ++i) {
        int key = static_cast<int>(rng() % 101) - 50;
        if (i == 0) key = INT_MIN;
        if (i == 1) key = INT_MAX;
        const auto value = "value_" + std::to_string(i);
        if (i < 2 || rng() % 2 == 0) {
            const bool is_new = expected.emplace(key, value).second;
            assert(avl_example::insert(avl, key, value) == is_new);
            rb.add(key, value);
        } else {
            const bool existed = expected.erase(key) != 0;
            assert(avl_example::erase(avl, key) == existed);
            rb.remove(key);
        }
        validate(avl, rb, expected);
        const auto it = expected.find(key);
        assert(rb.contains(key) == (it != expected.end()));
        if (it != expected.end()) assert(rb.findValueWithKey(key) == it->second);
        else {
            bool caught = false;
            try { (void)rb.findValueWithKey(key); }
            catch (const std::out_of_range&) { caught = true; }
            assert(caught);
        }
    }
    rb.clear();
    rb.validate({});
    rb[7] = "seven";
    rb.validate({{7, "seven"}});
}

void validate_hash(const ItemTable& table,
                   const std::map<std::size_t, std::string>& expected) {
    assert(table.size() == expected.size());
    for (std::size_t key = 0; key < 101; ++key) {
        const auto actual = table.find(key);
        const auto it = expected.find(key);
        assert(actual.has_value() == (it != expected.end()));
        if (actual) assert(*actual == it->second);
    }
    ++checked_states;
}

void check_hash_sequences() {
    bool caught = false;
    try { ItemTable impossible(0); }
    catch (const std::invalid_argument&) { caught = true; }
    assert(caught);
    ItemTable table(1); // Force every initial key into the same chain.
    std::map<std::size_t, std::string> expected;
    std::mt19937 rng(4035481);
    for (int i = 0; i < 4000; ++i) {
        const std::size_t key = rng() % 101;
        const auto value = std::to_string(i);
        if (rng() % 2 == 0) {
            const bool is_new = expected.count(key) == 0;
            expected[key] = value;
            assert(table.insert_or_assign(key, value) == is_new);
        } else {
            const bool existed = expected.erase(key) != 0;
            assert(table.erase(key) == existed);
        }
        if (i % 37 == 0) table.rehash(1 + rng() % 19);
        validate_hash(table, expected);
    }
    caught = false;
    try { table.rehash(0); }
    catch (const std::invalid_argument&) { caught = true; }
    assert(caught);
    validate_hash(table, expected);
    ItemTable copy = table;
    copy.insert_or_assign(1000, "independent");
    assert(!table.find(1000));
    ItemTable moved = std::move(table);
    validate_hash(moved, expected);
    table.insert_or_assign(1001, "reused");
    assert(table.find(1001) == std::optional<std::string>("reused"));
    ItemTable empty;
    assert(empty.size() == 0 && empty.load_factor() == 0);
    assert(!empty.find(1) && !empty.erase(1));
    empty.rehash(1);
    empty.insert_or_assign(1, "");
    assert(empty.find(1).has_value() && empty.find(1)->empty());
}

int main() {
    check_tree_sequences();
    check_hash_sequences();
    std::cout << "verified states: " << checked_states << '\n';
}
