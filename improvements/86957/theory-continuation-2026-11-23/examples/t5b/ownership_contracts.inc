// Author-only checks, appended to the exact class definitions from the lessons.
// No new learner exercise is introduced by this file.
#include <memory>
#include <type_traits>
#include <vector>

struct SharedItem {
    inline static int alive{0};
    teaching::weak_ptr<SharedItem> self;
    SharedItem() { ++alive; }
    ~SharedItem() { --alive; }
};

int main() {
    static_assert(!std::is_copy_constructible_v<LearningOwner<Item>>);
    static_assert(!std::is_copy_assignable_v<LearningOwner<Item>>);
    static_assert(std::is_nothrow_move_constructible_v<LearningOwner<Item>>);
    static_assert(std::is_nothrow_move_assignable_v<LearningOwner<Item>>);
    static_assert(!std::is_copy_constructible_v<std::unique_ptr<int>>);
    static_assert(std::is_same_v<decltype(*std::declval<const std::unique_ptr<int>&>()), int&>);
    static_assert(std::is_same_v<decltype(*std::declval<std::unique_ptr<const int>&>()), const int&>);
    static_assert(std::is_constructible_v<int&, int&>);
    static_assert(!std::is_constructible_v<int&, const int&>);
    static_assert(!std::is_constructible_v<int&, int>);
    static_assert(std::is_constructible_v<const int&, int>);
    static_assert(!std::is_constructible_v<int&&, int&>);
    static_assert(std::is_constructible_v<int&&, int>);
    static_assert(!std::is_constructible_v<int&&, const int&&>);
    int&& named = 7;
    static_assert(std::is_same_v<decltype((named)), int&>);
    static_assert(std::is_same_v<decltype(std::move(named)), int&&>);
    static_assert(std::is_same_v<decltype(("abc")), const char (&)[4]>);

    {
        LearningOwner<Item> empty;
        LearningOwner<Item> moved_empty{std::move(empty)};
        assert(!empty && !moved_empty);
        LearningOwner<Item> destination{new Item{5}};
        assert(Item::alive == 1);
        destination = std::move(moved_empty);
        assert(!destination && !moved_empty && Item::alive == 0);
    }
    assert(Item::alive == 0);

    {
        teaching::weak_ptr<SharedItem> empty;
        assert(empty.expired() && !empty.lock());
        teaching::weak_ptr<SharedItem> observer;
        {
            teaching::shared_ptr<SharedItem> owner{new SharedItem{}};
            owner->self = owner;
            observer = owner;
            auto copy = owner;
            assert(owner.use_count() == 2 && SharedItem::alive == 1);
            auto& alias = copy;
            copy = alias;
            assert(copy.use_count() == 2);
            auto moved = std::move(copy);
            assert(!copy && moved.use_count() == 2);
            owner.reset();
            auto locked = observer.lock();
            assert(locked && locked.use_count() == 2);
            moved.reset();
            assert(!observer.expired() && locked.use_count() == 1);
        }
        assert(SharedItem::alive == 0 && observer.expired());
        assert(!observer.lock());
        auto weak_copy = observer;
        assert(weak_copy.same_owner(observer));
        observer.reset();
        assert(weak_copy.expired() && !weak_copy.lock());
    }
    assert(SharedItem::alive == 0);

    {
        const std::vector<int> source{4, 5};
        std::vector<int> copy = std::move(source);
        copy[0] = 1;
        assert(source[0] == 4 && source.size() == 2 && copy[0] == 1);
        std::vector<int> empty;
        std::vector<int> moved = std::move(empty);
        assert(moved.empty());
        empty = {9};
        assert(empty[0] == 9);
    }
    std::cout << "ownership and reference contracts passed\n";
}
