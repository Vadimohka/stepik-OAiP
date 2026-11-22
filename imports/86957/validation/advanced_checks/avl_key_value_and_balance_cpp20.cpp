#include <memory>
#include <string>
#include <utility>

struct Node {
    int key;
    std::string value;
    std::shared_ptr<Node> left, right;
    int height = 1; // используется в AVL-дереве

    Node(int nKey, std::string nValue)
        : key(nKey), value(std::move(nValue)) {}
};

std::shared_ptr<Node> newNode(int key, std::string value) {
    return std::make_shared<Node>(key, std::move(value));
}

// Высота дерева
int getHeight(std::shared_ptr<Node> node) {
    if (!node)
        return 0;
    return node->height;
}

int max(int a, int b) {
    return (a > b) ? a : b;
}

// Правый поворот
std::shared_ptr<Node> rightRotate(std::shared_ptr<Node> node) {
    std::shared_ptr<Node> x = node->left;
    std::shared_ptr<Node> T2 = x->right;

    // Выполняем поворот
    x->right = node;
    node->left = T2;

    // Обновляем высоту 
    node->height = max(getHeight(node->left), getHeight(node->right)) + 1;
    x->height = max(getHeight(x->left), getHeight(x->right)) + 1;

    // Возвращаем новый корень 
    return x;
}

// Левый поворот
std::shared_ptr<Node> leftRotate(std::shared_ptr<Node> node) {
    std::shared_ptr<Node> y = node->right;
    std::shared_ptr<Node> T2 = y->left;

    // Выполняем поворот 
    y->left = node;
    node->right = T2;

    // Обновляем высоту
    node->height = max(getHeight(node->left), getHeight(node->right)) + 1;
    y->height = max(getHeight(y->left), getHeight(y->right)) + 1;

    // Возвращаем новый корень
    return y;
}

// Разность высот поддеревьев
int getBalance(std::shared_ptr<Node> node) {
    if (!node)
        return 0;
    return getHeight(node->left) - getHeight(node->right);
}

// Вставка
std::shared_ptr< Node> insert(std::shared_ptr<Node> node, int key, std::string value) {
    // 1: Выполняем обычную вставку BST 
    if (!node)
        return(newNode(key, value));

    if (key < node->key) {
        node->left = insert(node->left, key, value);
    }
    else if (key > node->key) {
        node->right = insert(node->right, key, value);
    }
    // Одинаковые ключи не допускаются 
    else {
        return node;
    }

    // 2: Обновляем высоту этого родительского узла 
    node->height = 1 + max(getHeight(node->left), getHeight(node->right));

    // 3: Получаем коэффициент баланса этого
    //    родительского узла, чтобы проверить,
    //    является ли этот узел сбалансированным 
    int balance = getBalance(node);

    // Если этот узел не сбалансирован,
    // то есть 4 случая:

    // Left Left Case 
    if (balance > 1 && key < node->left->key)
        return rightRotate(node);

    // Right Right Case 
    if (balance < -1 && key > node->right->key)
        return leftRotate(node);

    // Left Right Case 
    if (balance > 1 && key > node->left->key) {
        node->left = leftRotate(node->left);
        return rightRotate(node);
    }

    // Right Left Case 
    if (balance < -1 && key < node->right->key) {
        node->right = rightRotate(node->right);
        return leftRotate(node);
    }

    // возвращаем (неизменный) указатель узла
    return node;
}

// Минимальное значение в поддереве с корнем node.
std::shared_ptr< Node> minValueNode(std::shared_ptr<Node> node) {
    std::shared_ptr<Node> current = node;

    // Получаем самый левый лист
    while (current->left)
        current = current->left;

    return current;
}

// Удаление узла
std::shared_ptr< Node> deleteNode(std::shared_ptr<Node> root, int key) {
    // 1: Выполняем стандартное удаление
    if (!root)
        return root;

    // Если ключ удаляемого элемента меньше
    // ключа корня, тогда он лежит
    // в левом поддереве 
    if (key < root->key) {
        root->left = deleteNode(root->left, key);
    }

    // Если ключ удаляемого элемента больше
    // ключа корня, тогда он лежит
    // в правом поддереве 
    else if (key > root->key) {
        root->right = deleteNode(root->right, key);
    }

    // Если ключ совпадает с ключем корня
    // то это удаляемый элемент 
    else {
        // Узел имеет только одного потомка
        // Или не имеет ни одного 
        if ((!root->left) || (!root->right)) {
            std::shared_ptr<Node> temp = root->left ?
                root->left :
                root->right;

            // Нет потомка
            if (!temp) {
                temp = root;
                root = std::shared_ptr<Node>();
            }
            // Один потомок
            else {
                *root = *temp; // Копируем содержимое
                               // непустого потомка
            }
        }
        else {
            // Узел с двумя потомками: Получим преемника 
            // (минимальный в правом поддереве) 
            std::shared_ptr<Node> temp = minValueNode(root->right);

            // Копируем данные прееемника в этот узел
            root->key = temp->key;
            root->value = temp->value;

            // Удаляем преемника
            root->right = deleteNode(root->right, temp->key);
        }
    }

    // Если дерево имеет только один узел
    if (!root)
        return root;

    // 2: Обновляем высоту текущего узла 
    root->height = 1 + max(getHeight(root->left),
        getHeight(root->right));

    // 3: Получаем баланс-фактор этого узла
    // (чтобы проверить, стал ли этот узел несбалансированным)
    int balance = getBalance(root);

    // Если этот узел стал несбалансированным
    // То есть 4 случая

    // Left Left Case 
    if (balance > 1 && getBalance(root->left) >= 0)
        return rightRotate(root);

    // Left Right Case 
    if (balance > 1 && getBalance(root->left) < 0) {
        root->left = leftRotate(root->left);
        return rightRotate(root);
    }

    // Right Right Case 
    if (balance < -1 && getBalance(root->right) <= 0)
        return leftRotate(root);

    // Right Left Case 
    if (balance < -1 && getBalance(root->right) > 0) {
        root->right = rightRotate(root->right);
        return leftRotate(root);
    }

    return root;
}

#include <cassert>
#include <map>
#include <random>
#include <climits>
int validate(const std::shared_ptr<Node>& node, long long lo, long long hi, std::map<int,std::string>& got) {
    if (!node) return 0;
    assert(node->key>lo && node->key<hi);
    int l=validate(node->left,lo,node->key,got), r=validate(node->right,node->key,hi,got);
    assert(l-r<=1 && r-l<=1); assert(node->height==1+std::max(l,r));
    got.emplace(node->key,node->value); return node->height;
}
void checkTree(const std::shared_ptr<Node>& root,const std::map<int,std::string>& expected) {
    std::map<int,std::string> actual; validate(root,LLONG_MIN,LLONG_MAX,actual); assert(actual==expected);
}
int main() {
    std::shared_ptr<Node> root; std::map<int,std::string> expected;
    for (auto [key,value]:std::map<int,std::string>{{1,"one"},{2,"two"},{3,"three"}}) {
        root=insert(root,key,value);expected.emplace(key,value);checkTree(root,expected);
    }
    root=deleteNode(root,2);expected.erase(2);checkTree(root,expected);
    assert(root->key==3 && root->value=="three");
    std::mt19937 random(42);
    for (int i=0;i<500;++i) {
        int key=static_cast<int>(random()%50);
        if (random()%2) { auto value=std::to_string(i); root=insert(root,key,value);expected.emplace(key,value); }
        else {root=deleteNode(root,key);expected.erase(key);}
        checkTree(root,expected);
    }
    for (int key=0;key<50;++key) {root=deleteNode(root,key);expected.erase(key);checkTree(root,expected);}
    assert(!root);
}
