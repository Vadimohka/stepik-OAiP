"""Bounded invariant checks of the current tree and smart-pointer examples.

These checks provide executed coverage, not a proof of correctness for all
inputs. Iterator extension fragments are deliberately not claimed as complete.
"""
import json
from course_blocks import blocks, rbt
from validate_advanced import HERE, compile_case, execute, results

RBT_CHECK = r'''
#include <algorithm>
#include <cassert>
#include <climits>
#include <iostream>
#include <map>
#include <random>
#include <set>
#include <string>
struct CheckedRBT : RBT<int,std::string> {
    int visit(shared_ptr<Node> node, shared_ptr<Node> parent, long long low,
              long long high, std::set<const Node*>& seen, std::map<int,std::string>& actual) {
        if (!node) return 1;
        assert(seen.insert(node.get()).second);
        assert(node->parent.lock() == parent);
        assert(low < node->key && node->key < high);
        actual.emplace(node->key, node->data);
        if (!node->color) {
            assert(!node->left || node->left->color);
            assert(!node->right || node->right->color);
        }
        int left = visit(node->left,node,low,node->key,seen,actual);
        int right = visit(node->right,node,node->key,high,seen,actual);
        assert(left == right);
        return left + int(node->color);
    }
    void verify(const std::map<int,std::string>& expected) {
        assert(!root || (root->color && root->parent.expired()));
        std::set<const Node*> seen;
        std::map<int,std::string> actual;
        visit(root,{},LLONG_MIN,LLONG_MAX,seen,actual);
        assert(actual == expected);
        for (const auto& [k,v] : expected) assert(findValueWithKey(k) == v);
    }
};
int main(){
    std::mt19937 rng(86957);
    CheckedRBT tree;
    std::map<int,std::string> expected;
    for(int i=0; i<20000; ++i) {
        int key = int(rng()%201)-100;
        if(rng()%2) { auto value=std::to_string(i); tree.add(key,value); expected.emplace(key,value); }
        else { tree.remove(key); expected.erase(key); }
        tree.verify(expected);
    }
    while(!expected.empty()) { int key=expected.begin()->first; tree.remove(key); expected.erase(key); tree.verify(expected); }
    tree.remove(42); tree.verify(expected);
    std::cout << "RBT: 20000 deterministic mixed operations, values, parent links and color invariants passed\n";
}
'''

AVL_CHECK = r'''
#include <algorithm>
#include <cassert>
#include <climits>
#include <iostream>
#include <map>
#include <random>
#include <set>
int visit(std::shared_ptr<Node> node,long long low,long long high,
          std::set<const Node*>& seen,std::map<int,std::string>& actual) {
    if(!node) return 0;
    assert(seen.insert(node.get()).second);
    assert(low < node->key && node->key < high);
    actual.emplace(node->key,node->value);
    int left=visit(node->left,low,node->key,seen,actual);
    int right=visit(node->right,node->key,high,seen,actual);
    assert(std::abs(left-right)<=1);
    assert(node->height==1+std::max(left,right));
    return node->height;
}
void verify(std::shared_ptr<Node> root,const std::map<int,std::string>& expected) {
    std::set<const Node*> seen;std::map<int,std::string> actual;
    visit(root,LLONG_MIN,LLONG_MAX,seen,actual);assert(actual==expected);
}
int main(){
    std::mt19937 rng(86957);std::shared_ptr<Node> root;
    std::map<int,std::string> expected;
    for(int i=0;i<20000;++i){
        int key=int(rng()%201)-100;
        if(rng()%2){auto value=std::to_string(i);root=insert(root,key,value);expected.emplace(key,value);}
        else{root=deleteNode(root,key);expected.erase(key);}
        verify(root,expected);
    }
    while(!expected.empty()){int key=expected.begin()->first;root=deleteNode(root,key);expected.erase(key);verify(root,expected);}
    root=deleteNode(root,42);verify(root,expected);
    std::cout << "AVL: 20000 deterministic mixed operations, values, heights and balance passed\n";
}
'''

SHARED_CHECK = r'''
#include <cassert>
#include <iostream>
struct Item {
    inline static int alive=0;
    teaching::weak_ptr<Item> self;
    teaching::shared_ptr<Item> child;
    Item(){++alive;} ~Item(){--alive;}
};
int main(){
    teaching::weak_ptr<Item> outside;
    {
        teaching::shared_ptr<Item> root(new Item);
        root->self=root; outside=root;
        { auto copy=root; assert(root.use_count()==2); copy=copy; assert(root.use_count()==2); }
        assert(root.use_count()==1);
        root->child=teaching::shared_ptr<Item>(new Item);
        root=std::move(root->child);
        assert(Item::alive==1);
        assert(outside.expired() && !outside.lock());
        root->self=root;outside=root;
    }
    assert(Item::alive==0 && outside.expired() && !outside.lock());
    auto copy=outside;assert(copy.same_owner(outside));outside.reset();copy.reset();
    teaching::shared_ptr<Item> empty;assert(empty.use_count()==0 && !empty);
    std::cout << "teaching shared_ptr/weak_ptr: lifetime, self-weak, copy, nested move and expired lock passed\n";
}
'''

if __name__ == '__main__':
    try:
        exe, _ = compile_case('rbt_current_invariants', rbt(True)+RBT_CHECK, sanitize=True)
        execute('rbt_current_invariants', exe)
        exe, _ = compile_case('avl_current_invariants', blocks(3570281)[0]+AVL_CHECK, sanitize=True)
        execute('avl_current_invariants', exe)
        exe, _ = compile_case('shared_current_lifetime', blocks(3570213)[0]+SHARED_CHECK, sanitize=True)
        execute('shared_current_lifetime', exe)
    finally:
        (HERE/'invariant_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print('Passed invariant compilation/runtime checks:',len(results))
