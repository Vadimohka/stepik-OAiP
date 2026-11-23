// Author-only observations of the exact saved RBT implementation.
// verify.py adds read-only observation calls in a temporary header; it also
// proves that removing those calls recovers the lesson header byte for byte.
#include <algorithm>
#include <cassert>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

namespace advanced_trace {
constexpr int absent = -9999;
bool enabled = false;
int removed_key = absent;

struct Event {
    std::string stage;
    int key, parent, root, left, right, sibling;
    bool parent_black, left_black, right_black;
    std::vector<int> physical_paths, conceptual_paths, left_branch, right_branch;
};
std::vector<Event> events;

// Counts include the starting node when black and the final black NIL.
// For deletion, the still-attached doomed leaf is conceptually one NIL.
template<class Node>
void count_paths(const std::shared_ptr<Node>& node, int count,
                 bool conceptual, std::vector<int>& result) {
    if (!node || (conceptual && node->key == removed_key)) {
        if (node) assert(!node->left && !node->right);
        result.push_back(count + 1);
        return;
    }
    count += node->color ? 1 : 0;
    count_paths(node->left, count, conceptual, result);
    count_paths(node->right, count, conceptual, result);
}

template<class Node>
std::vector<int> counts(const std::shared_ptr<Node>& node, bool conceptual) {
    std::vector<int> result;
    count_paths(node, 0, conceptual, result);
    std::sort(result.begin(), result.end());
    result.erase(std::unique(result.begin(), result.end()), result.end());
    return result;
}

template<class Node>
void observe(const char* stage, const std::shared_ptr<Node>& node,
             const std::shared_ptr<Node>& root) {
    if (!enabled) return;
    const auto parent = node->parent.lock();
    const auto sibling = parent ? (parent->left == node ? parent->right : parent->left)
                                : std::shared_ptr<Node>{};
    events.push_back({stage, node->key, parent ? parent->key : absent,
                      root ? root->key : absent,
                      node->left ? node->left->key : absent,
                      node->right ? node->right->key : absent,
                      sibling ? sibling->key : absent,
                      !parent || parent->color,
                      !node->left || node->left->color,
                      !node->right || node->right->color,
                      counts(root, false), counts(root, true),
                      parent ? counts(parent->left, true) : std::vector<int>{},
                      parent ? counts(parent->right, true) : std::vector<int>{}});
}
} // namespace advanced_trace

#include "rbt_instrumented.hpp"

class Inspector : public RBT<int, int> {
    using Pointer = std::shared_ptr<Node>;

    int check_node(const Pointer& node, const Pointer& parent,
                   std::vector<int>& keys) const {
        if (!node) return 1;
        assert(node->parent.lock() == parent);
        if (!node->color) {
            assert(!node->left || node->left->color);
            assert(!node->right || node->right->color);
        }
        const int left = check_node(node->left, node, keys);
        keys.push_back(node->key);
        const int right = check_node(node->right, node, keys);
        assert(left == right);
        return left + (node->color ? 1 : 0);
    }

public:
    void expect(const std::vector<int>& expected, int black_count) const {
        assert(!root || root->color);
        assert(!root || root->parent.expired());
        std::vector<int> keys;
        assert(check_node(root, {}, keys) == black_count);
        assert(keys == expected);
    }
    void expect_shape(int top, int left, int right) const {
        assert(root && root->key == top && root->color);
        assert(root->left && root->left->key == left && root->left->color);
        assert(root->right && root->right->key == right && root->right->color);
    }
};

void insertion() {
    using namespace advanced_trace;
    Inspector tree;
    for (int key : {10, 5, 15, 1, 7, 12, 18}) tree.add(key, key);
    tree.expect({1, 5, 7, 10, 12, 15, 18}, 3);
    enabled = true;
    tree.add(0, 0);
    enabled = false;
    assert(events.size() == 3);
    assert(events[0].stage == "insert_case2" && events[0].key == 0);
    assert(events[0].parent == 1 && !events[0].parent_black);
    assert(events[1].stage == "insert_case3_up" && events[1].key == 5);
    assert(events[2].stage == "insert_case2" && events[2].key == 5);
    for (std::size_t i : {std::size_t{1}, std::size_t{2}}) {
        const auto& event = events[i];
        assert(event.parent == 10 && event.parent_black);
        assert(event.left == 1 && event.right == 7);
        assert(event.left_black && event.right_black);
    }
    for (const auto& event : events) {
        assert(event.physical_paths == std::vector<int>{3});
    }
    tree.expect({0, 1, 5, 7, 10, 12, 15, 18}, 3);
    std::cout << "insert_case2(0,parent=1:red)\n"
                 "insert_case3_up(5,children=1:black,7:black)\n"
                 "insert_case2(5,parent=10:black)\n"
                 "root-to-NIL black counts: before=3, recolor=3, after=3\n";
}

void deletion(bool mirror) {
    using namespace advanced_trace;
    Inspector tree;
    const std::vector<int> order = mirror ? std::vector<int>{10, 20, 5, 7}
                                         : std::vector<int>{10, 5, 20, 15};
    for (int key : order) tree.add(key, key);
    tree.expect(mirror ? std::vector<int>{5, 7, 10, 20}
                       : std::vector<int>{5, 10, 15, 20}, 3);
    tree.expect_shape(10, 5, 20);
    removed_key = mirror ? 20 : 5;
    enabled = true;
    tree.remove(removed_key);
    enabled = false;
    assert(events.size() == 4);
    const std::vector<std::string> stages{
        "delete_case5_before", "delete_case5_after",
        "delete_case6_before", "delete_case6_after"};
    for (std::size_t i = 0; i < events.size(); ++i) {
        assert(events[i].stage == stages[i]);
        assert(events[i].key == removed_key);
    }
    assert(events[0].sibling == (mirror ? 5 : 20));
    assert(events[1].sibling == (mirror ? 7 : 15));
    for (std::size_t i = 0; i < 3; ++i) {
        const auto& event = events[i];
        assert(event.root == 10);
        assert(event.physical_paths == std::vector<int>{3});
        assert((event.conceptual_paths == std::vector<int>{2, 3}));
        assert(event.left_branch == std::vector<int>{mirror ? 2 : 1});
        assert(event.right_branch == std::vector<int>{mirror ? 1 : 2});
    }
    // After case 6 the conceptual deficit is gone. The temporary doomed node
    // remains physically attached until remove() resumes and disconnects it.
    assert(events[3].root == (mirror ? 7 : 15));
    assert(events[3].conceptual_paths == std::vector<int>{3});
    assert((events[3].physical_paths == std::vector<int>{3, 4}));
    tree.expect(mirror ? std::vector<int>{5, 7, 10} : std::vector<int>{10, 15, 20}, 3);
    tree.expect_shape(mirror ? 7 : 15, mirror ? 5 : 10, mirror ? 10 : 20);
    assert(!tree.contains(removed_key));
    std::cout << (mirror ? "delete-right: 20\n" : "delete-left: 5\n")
              << "before deletion: branch counts=2/2\n"
              << (mirror ? "case5 before/after: branch counts=2/1 -> 2/1\n"
                         : "case5 before/after: branch counts=1/2 -> 1/2\n")
              << "case6: conceptual root-to-NIL counts=3\n"
                 "case6: attached-placeholder counts=3,4\n"
                 "after detach: root-to-NIL counts=3\n";
}

int main(int argc, char** argv) {
    if (argc != 2) return 1;
    const std::string mode = argv[1];
    if (mode == "insertion") insertion();
    else if (mode == "deletion-left") deletion(false);
    else if (mode == "deletion-right") deletion(true);
    else return 1;
}
