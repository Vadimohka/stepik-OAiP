#include <memory>
#include <stdexcept>
#include <utility>

using std::shared_ptr;
using std::weak_ptr;

template<class T, class T1>
class RBT {
public:
    RBT() = default;
    ~RBT() = default;
    RBT(const RBT&) = delete;
    RBT& operator=(const RBT&) = delete;
    void add(T key, T1 value);
    void remove(T key);
    T1 findValueWithKey(T key) {
        auto node = find(root, key);
        if (!node) throw std::out_of_range("key not found");
        return node->data;
    }
    bool contains(T key) { return static_cast<bool>(find(root, key)); }
    T1& operator[](T key) {
        add(key, T1{});
        return find(root, key)->data;
    }
    void clear() { root.reset(); }

protected:

    struct Node {
        Node(T nKey, T1 nValue)
            : color(false), key(std::move(nKey)), data(std::move(nValue)) {}
        Node() : color(true), key{}, data{} {} // чёрный служебный узел
        shared_ptr<Node> left, right;
        weak_ptr<Node> parent; // родитель не создаёт цикл владения
        bool color; // red = false, black = true
        T key;
        T1 data;
    };

    shared_ptr<Node> grandparent(shared_ptr<Node> node);
    shared_ptr<Node> uncle(shared_ptr<Node> node);
    shared_ptr<Node> sibling(shared_ptr<Node> node);

    void RotateLeft(shared_ptr<Node> node);
    void RotateRight(shared_ptr<Node> node);

    void InsCase1(shared_ptr<Node> node);
    void InsCase2(shared_ptr<Node> node);
    void InsCase3(shared_ptr<Node> node);
    void InsCase4(shared_ptr<Node> node);
    void InsCase5(shared_ptr<Node> node);

    void DelCase1(shared_ptr<Node> node);
    void DelCase2(shared_ptr<Node> node);
    void DelCase3(shared_ptr<Node> node);
    void DelCase4(shared_ptr<Node> node);
    void DelCase5(shared_ptr<Node> node);
    void DelCase6(shared_ptr<Node> node);

    shared_ptr<Node> find(shared_ptr<Node> node, T key) {
        while (node) {
            if (key < node->key) node = node->left;
            else if (key > node->key) node = node->right;
            else return node;
        }
        return {};
    }

    shared_ptr<Node> min(shared_ptr<Node> node) {
        while (node && node->left) node = node->left;
        return node;
    }
    shared_ptr<Node> max(shared_ptr<Node> node) {
        while (node && node->right) node = node->right;
        return node;
    }
   
protected:
    shared_ptr<Node> root;
};

template<class T, class T1>
shared_ptr<typename RBT<T, T1>::Node> RBT<T, T1>::grandparent(shared_ptr<Node> node) {
    shared_ptr<Node> p = node->parent.lock(); // удерживаем родителя локальным shared_ptr
    if (p && !p->parent.expired()) {
        return p->parent.lock();
    } else {
        return shared_ptr<Node>();
    }
}

template<class T, class T1>
shared_ptr<typename RBT<T, T1>::Node> RBT<T, T1>::uncle(shared_ptr<Node> node) {
    shared_ptr<Node> tmp = grandparent(node);

    if (tmp) {
        if ((tmp->left == node->parent.lock())) {
            return tmp->right;
        } else {
            return tmp->left;
        }
    } else {
        return shared_ptr<Node>();
    }
}

template<class T, class T1> // Так же, как и в АВЛ-дереве
void RBT<T, T1>::RotateLeft(shared_ptr<Node> node) {
    shared_ptr<Node> right = node->right;

    right->parent = node->parent.lock();
    if (!node->parent.expired()) {
        shared_ptr<Node> p = node->parent.lock();

        if ((p->left == node)) {
            p->left = right;
        } else {
            p->right = right;
        }
    } else {
        root = right;
    }

    node->right = right->left;
    if (right->left) {
        right->left->parent = node;
    }

    node->parent = right;
    right->left = node;
}

template<class T, class T1> // Так же, как и в АВЛ-дереве
void RBT<T, T1>::RotateRight(shared_ptr<Node> node) {
    shared_ptr<Node> left = node->left;

    left->parent = node->parent.lock();
    if (!node->parent.expired()) {
        shared_ptr<Node> p = node->parent.lock();

        if ((p->left == node)) {
            p->left = left;
        } else {
            p->right = left;
        }
    } else {
        root = left;
    }

    node->left = left->right;
    if (left->right) {
        left->right->parent = node;
    }

    node->parent = left;
    left->right = node;
}

template<class T, class T1>
void RBT<T, T1>::add(T key, T1 value) {
    shared_ptr<Node> tmp = root, p = shared_ptr<Node>();

    // Спускаемся по дереву, ищя, куда вставить новый узел
    while (tmp) {
        p = tmp;

        if (tmp->key > key) {
            tmp = tmp->left;
        } else if (tmp->key < key) {
            tmp = tmp->right;
        } else {
            return;// Если такой узел уже есть, то прото выходим
        }
    }

    tmp = shared_ptr<Node>(new Node(key, value));
    tmp->parent = p;

    if (p) {
        if (tmp->key > p->key) {
            p->right = tmp;
        } else {
            p->left = tmp;
        }
    } else {
        root = tmp;
    }

    InsCase1(tmp);
    return;
} 

template<class T, class T1>
void RBT<T, T1>::InsCase1(shared_ptr<Node> node) {
    if (node->parent.expired()) {
        node->color = 1;
    }
    else {
        InsCase2(node);
    }
}

template<class T, class T1>
void RBT<T, T1>::InsCase2(shared_ptr<Node> node) {
    if (node->parent.lock()->color) {
        return;
    } else {
        InsCase3(node);
    } 
}

template<class T, class T1>
void RBT<T, T1>::InsCase3(shared_ptr<Node> node) {
    shared_ptr<Node> u = uncle(node);

    if (u && !u->color) {
        node->parent.lock()->color = 1;
        u->color = 1;
        shared_ptr<Node> g = grandparent(node);
        g->color = 0;
        InsCase1(g);
    } else {
        InsCase4(node);
    }
}

template<class T, class T1>
void RBT<T, T1>::InsCase4(shared_ptr<Node> node) {
    shared_ptr<Node> g = grandparent(node), tmp = node;
    shared_ptr<Node> p = node->parent.lock();
    if ((node == p->right) && (p == g->left)) {
        RotateLeft(p);
        tmp = node->left;
    } else if ((node == p->left) && (p == g->right)) {
        RotateRight(p);
        tmp = node->right;
    }

    InsCase5(tmp);
}

template<class T, class T1>
void RBT<T, T1>::InsCase5(shared_ptr<Node> node) {
    shared_ptr<Node> g = grandparent(node);
    shared_ptr<Node> p = node->parent.lock();
    p->color = 1;
    g->color = 0;

    if ((node == p->left)) {
        RotateRight(g);
    } else {
        RotateLeft(g);
    }
}

template<class T, class T1>
shared_ptr<typename RBT<T, T1>::Node> RBT<T, T1>::sibling(shared_ptr<Node> node) {
    if (node->parent.expired()) {
        return shared_ptr<Node>();
    }

    shared_ptr<Node> p = node->parent.lock();

    if ((node == p->left)) {
        return p->right;
    } else {
        return p->left;
    }
}

template<class T, class T1>
void RBT<T, T1>::remove(T key) {
    shared_ptr<Node> tmp = root ? find(root, key) : shared_ptr<Node>(); // Ищем узел с нужным ключем
    // Повезло повезло, ниче делать не надо если такого узла нет
    if (!tmp) {
        return;
    }

    // Случай, когда дерево состоит из одного узла
    if (tmp->parent.expired() && !tmp->left && !tmp->right) {
        root = shared_ptr<Node>(); // Обнуляем корень
        return;
    }

    // Если у узла есть и левый и правый потомок
    if (tmp->left && tmp->right)  {
        // Ищем самый правый узел в левом поддереве
        // Этот узел будет ближайшим меньшим к удаляемому, по значнию ключа
        // Что дает нам возможность переместить его значение в удаляемый узел, и удалять уже новый, но у которого будет либо один, либо ноль потомков
        // При таком способе прийдется рассматривать намного меньшее количество вариантов
        shared_ptr<Node> removed = tmp->left;
        while (removed->right) {
            removed = removed->right;
        }
        tmp->data = removed->data;
        tmp->key = removed->key;
        tmp = removed;
    }
    shared_ptr<Node> child = tmp->left ? tmp->left : tmp->right; 
    // Ищем потомка, если таково имеется
    // Случай, когда потомков нет
    if (!child) {
        if (tmp->color) {// Удаление красного узла не привело бы к разбалансировке дерева
            DelCase1(tmp); // А вот удаление черного узла нарушает свойства красно-черного дерева об одинаковой длинне черных путей
        }
        shared_ptr<Node> p = tmp->parent.lock();

        if ((p->left == tmp)) {// Меняем связи, тем самым удаляя узел, после чего тот выйдет из области видимости
            p->left = child;
        } else {
            p->right = child;
        }
    }
    // Случай, когда потомок есть
    else {
        child->parent = tmp->parent.lock(); // Меняем связи
        shared_ptr<Node> p = tmp->parent.lock();

        // Меняем связи
        if (!tmp->parent.expired()) {
            if ((tmp == p->left)) {
                p->left = child;
            } else {
                p->right = child;
            }
        } else {
            root = child; // Если надо, меняем корень дерева
        }
        // Если удаляемы узел был красным, то никакие свойства не нарушаются
        if (tmp->color) {
            if (!child->color) {// Если удаляемый узел был черным, а потомок красный, то можем сохранить свойстав дерева, перекрасив потомка в черныйё
                child->color = 1;
            } else {
                DelCase1(child);
            }
        }
    }
}

template<class T, class T1>
void RBT<T, T1>::DelCase1(shared_ptr<Node> node) {
    if (!node->parent.expired()) {
        DelCase2(node);
    }
}

template<class T, class T1>
void RBT<T, T1>::DelCase2(shared_ptr<Node> node) {
    shared_ptr<Node> s = sibling(node);
    shared_ptr<Node> p = node->parent.lock();
    bool scol = s ? s->color : 1;

    if (!scol) {
        p->color = 0;
        s->color = 1;

        if ((node == p->left)) {
            RotateLeft(p);
        } else {
            RotateRight(p);
        }
    }

    DelCase3(node);
}

template<class T, class T1>
void RBT<T, T1>::DelCase3(shared_ptr<Node> node) {
    shared_ptr<Node> s = sibling(node);
    shared_ptr<Node> p = node->parent.lock();

    bool scol = s ? s->color : 1;
    bool lcol = s && s->left ? s->left->color : 1;
    bool rcol = s && s->right ? s->right->color : 1;

    if (p->color && scol && lcol && rcol) {
        if (s) {
           s->color = 0;
        }
        DelCase1(p);
    } else {
        DelCase4(node);
    }
}

template<class T, class T1>
void RBT<T, T1>::DelCase4(shared_ptr<Node> node) {
    shared_ptr<Node> s = sibling(node);
    shared_ptr<Node> p = node->parent.lock();

    bool scol = s ? s->color : 1;
    bool lcol = s && s->left ? s->left->color : 1;
    bool rcol = s && s->right ? s->right->color : 1;

    if (!p->color && scol && lcol && rcol) {
        if (s) {
            s->color = 0;
        }
        p->color = 1;
    } else {
        DelCase5(node);
    }
}

template<class T, class T1>
void RBT<T, T1>::DelCase5(shared_ptr<Node> node) {
    shared_ptr<Node> s = sibling(node);
    shared_ptr<Node> p = node->parent.lock();

    bool lcol = s->left ? s->left->color : 1;
    bool rcol = s->right ? s->right->color : 1;

    if (s->color) {
        if ((node == p->left) && rcol && !lcol) {
            s->color = 0;
            s->left->color = 1;
            RotateRight(s);
        } else if ((node == p->right) && lcol && !rcol) {
            s->color = 0;
            s->right->color = 1;
            RotateLeft(s);
        }
    }

    DelCase6(node);
}

template<class T, class T1>
void RBT<T, T1>::DelCase6(shared_ptr<Node> node) {
    shared_ptr<Node>  s = sibling(node);
    shared_ptr<Node> p = node->parent.lock();
    s->color = p->color;
    p->color = 1;

    if ((node == p->left)) {
        if (s->right) {
            s->right->color = 1;
        }
        RotateLeft(p);
    } else {
        if (s->left) {
            s->left->color = 1;
        }
        RotateRight(p);
    }
}

#include <type_traits>
static_assert(!std::is_copy_constructible_v<RBT<int,int>>);
static_assert(!std::is_copy_assignable_v<RBT<int,int>>);
static_assert(!std::is_move_constructible_v<RBT<int,int>>);
static_assert(!std::is_move_assignable_v<RBT<int,int>>);
int main(){ RBT<int,int> a; a.add(2,20); a[1]=10;
    a.add(2,30); if(a.findValueWithKey(2)!=20) return 1;
    a.remove(99); a.remove(2); if(a.contains(2)) return 2;
    try { (void)a.findValueWithKey(2); return 3; } catch(const std::out_of_range&) {}
    a.clear(); return a.contains(1) ? 4 : 0;
}
