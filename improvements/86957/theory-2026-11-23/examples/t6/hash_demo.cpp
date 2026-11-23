#include "hash_table.hpp"
#include <iostream>

int main() {
    ItemTable items(4);
    items.insert_or_assign(1, "pencil");
    items.insert_or_assign(5, "notebook");
    items.insert_or_assign(9, "ruler");
    items.insert_or_assign(5, "book");
    std::cout << items.size() << ' ' << items.load_factor() << '\n';
    if (const auto name = items.find(5)) std::cout << *name << '\n';
    items.rehash(8);
    items.erase(1);
    std::cout << items.size() << ' ' << items.bucket_count() << '\n';
    std::cout << std::boolalpha << items.find(1).has_value() << '\n';
}
