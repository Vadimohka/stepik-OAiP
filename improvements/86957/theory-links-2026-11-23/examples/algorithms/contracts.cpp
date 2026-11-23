// Author-only checks for LINKS: public result contracts and value ownership.
#include "bst_prefix.hpp"
#include "avl.hpp"
#include "rbt.hpp"
#include "hash_table.hpp"
#include <cassert>
#include <iostream>
#include <string>
#include <type_traits>
#include <utility>

int main() {
    static_assert(std::is_same_v<decltype(insert_bst(
        std::declval<std::unique_ptr<BstNode>&>(), 1, std::string{})), bool>);
    static_assert(std::is_same_v<decltype(avl_example::insert(
        std::declval<avl_example::Tree&>(), 1, std::string{})), bool>);
    static_assert(std::is_same_v<decltype(std::declval<RBT<int, std::string>&>()
        .add(1, std::string{})), void>);

    std::unique_ptr<BstNode> bst;
    assert(insert_bst(bst, 2, "two"));
    assert(!insert_bst(bst, 2, "replacement"));
    assert(bst->value == "two");
    assert(insert_bst(bst, 1, "one"));
    assert(insert_bst(bst, 3, "three"));
    assert(!insert_bst(bst, 1, "replacement"));
    assert(bst->left->value == "one");
    std::cout << "BST: bool; duplicates preserve values\n";

    avl_example::Tree avl;
    for (int key : {3, 2, 1}) {
        assert(avl_example::insert(avl, key, std::to_string(key)));
    }
    assert(avl->key == 2); // The insertion sequence actually causes balancing.
    assert(!avl_example::insert(avl, 2, "replacement"));
    assert(avl_example::find(avl, 2)->value == "2");
    assert(avl_example::erase(avl, 2));
    assert(avl_example::insert(avl, 2, "new"));
    assert(avl_example::find(avl, 2)->value == "new");
    std::cout << "AVL: bool; duplicate and reinsert contracts\n";

    RBT<int, std::string> rb;
    assert(!rb.contains(2));
    for (int key : {1, 2, 3}) rb.add(key, std::to_string(key));
    rb.add(2, "replacement");
    assert(rb.findValueWithKey(2) == "2");
    rb.remove(2);
    rb.add(2, "new");
    assert(rb.findValueWithKey(2) == "new");
    std::cout << "RB: void; duplicate and reinsert contracts\n";

    ItemTable items(1); // Every key collides.
    assert(!items.find(5));
    assert(items.insert_or_assign(1, "one"));
    assert(items.insert_or_assign(5, "original"));
    auto value = items.find(5);
    assert(value && *value == "original");
    assert(!items.insert_or_assign(5, "changed"));
    assert(*value == "original");
    assert(*items.find(5) == "changed");
    items.rehash(8);
    assert(items.erase(5));
    assert(!items.find(5));
    assert(*value == "original");
    assert(*items.find(1) == "one");
    std::cout << "ItemTable: returned copy survives update, rehash and erase\n";
}
