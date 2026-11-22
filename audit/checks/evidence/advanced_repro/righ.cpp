#include <memory>
struct Node {std::shared_ptr<Node> parent;}; void rotate(std::shared_ptr<Node> node,std::shared_ptr<Node> right){node->parent=righ;}
