#include <cassert>
#include <iostream>
#include <utility>

template<class T>
class LearningOwner {
public:
    explicit LearningOwner(T* pointer = nullptr) noexcept : pointer_{pointer} {}

    ~LearningOwner() {
        delete pointer_;
    }

    LearningOwner(const LearningOwner&) = delete;
    LearningOwner& operator=(const LearningOwner&) = delete;

    LearningOwner(LearningOwner&& other) noexcept : pointer_{other.pointer_} {
        other.pointer_ = nullptr;
    }

    LearningOwner& operator=(LearningOwner&& other) noexcept {
        if (this != &other) {
            T* incoming = other.pointer_;
            other.pointer_ = nullptr;
            delete pointer_;
            pointer_ = incoming;
        }
        return *this;
    }

    explicit operator bool() const noexcept {
        return pointer_ != nullptr;
    }

    T& operator*() const {
        return *pointer_;
    }

    T* operator->() const noexcept {
        return pointer_;
    }

private:
    T* pointer_;
};

struct Item {
    inline static int alive{0};
    int value;
    LearningOwner<Item> child;

    explicit Item(int initial) : value{initial} {
        ++alive;
    }

    ~Item() {
        --alive;
    }
};

int main() {
    {
        LearningOwner<Item> first{new Item{42}};
        LearningOwner<Item> second{std::move(first)};
        assert(!first && second);

        LearningOwner<Item> third{new Item{7}};
        third = std::move(second);
        assert(!second && Item::alive == 1);

        LearningOwner<Item>& same = third;
        third = std::move(same);
        assert(third && Item::alive == 1);
        assert((*third).value == 42);
        std::cout << third->value << '\n';
    }
    assert(Item::alive == 0);
    std::cout << Item::alive << '\n';

    {
        LearningOwner<Item> root{new Item{1}};
        root->child = LearningOwner<Item>{new Item{2}};
        assert(Item::alive == 2);

        root = std::move(root->child);
        assert(root && root->value == 2 && Item::alive == 1);
        std::cout << root->value << '\n';
    }
    assert(Item::alive == 0);
    std::cout << Item::alive << '\n';
}
