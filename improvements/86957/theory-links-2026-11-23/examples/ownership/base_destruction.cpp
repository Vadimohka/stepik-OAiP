// Author verification only. This is not a new Stepik learner assignment.
#include <cassert>
#include <iostream>
#include <memory>
#include <string>
#include <type_traits>
#include <utility>

struct PolyBase {
    inline static int alive = 0;
    PolyBase() { ++alive; }
    virtual ~PolyBase() { --alive; }
};

struct PolyDerived : PolyBase {
    inline static int alive = 0;
    PolyDerived() { ++alive; }
    ~PolyDerived() override { --alive; }
};

struct Base {
    inline static int alive = 0;
    Base() { ++alive; }
    ~Base() { --alive; }
};

struct Derived : Base {
    inline static int alive = 0;
    Derived() { ++alive; }
    ~Derived() { --alive; }
};

static_assert(std::has_virtual_destructor_v<PolyBase>);
static_assert(!std::has_virtual_destructor_v<Base>);

void unique_normal() {
    std::unique_ptr<PolyBase> first = std::make_unique<PolyDerived>();
    PolyBase* observer = first.get();
    std::unique_ptr<PolyBase> second = std::move(first);
    assert(!first && second.get() == observer);
    assert(PolyBase::alive == 1 && PolyDerived::alive == 1);
    second.reset();
    observer = nullptr;
    assert(!second && observer == nullptr);
    assert(PolyBase::alive == 0 && PolyDerived::alive == 0);
}

void unique_empty() {
    std::unique_ptr<PolyBase> first;
    std::unique_ptr<PolyBase> second = std::move(first);
    assert(!first && !second);
    second.reset();
    second = std::make_unique<PolyDerived>();
    assert(PolyDerived::alive == 1);
    second = std::move(first); // Replacing a resource with an empty owner.
    assert(!first && !second);
    assert(PolyBase::alive == 0 && PolyDerived::alive == 0);
}

void shared_convert() {
    auto typed = std::make_shared<Derived>();
    std::shared_ptr<Base> base = typed;
    std::weak_ptr<Base> weak = base;
    assert(base.use_count() == 2);
    assert(!typed.owner_before(base) && !base.owner_before(typed));
    typed.reset();
    assert(Base::alive == 1 && Derived::alive == 1);
    auto held = weak.lock();
    base.reset();
    assert(held && !weak.expired());
    held.reset();
    assert(Base::alive == 0 && Derived::alive == 0);
    assert(weak.expired() && !weak.lock());
}

void shared_direct() {
    // The constructor receives Derived*, so destruction retains Derived.
    // Passing an already converted Base* here would be a different contract.
    std::shared_ptr<Base> owner{new Derived{}};
    assert(Base::alive == 1 && Derived::alive == 1);
    owner.reset();
    assert(Base::alive == 0 && Derived::alive == 0);
    owner.reset(); // Empty reset must not destroy anything a second time.
    assert(Base::alive == 0 && Derived::alive == 0);
}

int main(int argc, char* argv[]) {
    if (argc != 2) return 2;
    const std::string name = argv[1];
    if (name == "unique_normal") unique_normal();
    else if (name == "unique_empty") unique_empty();
    else if (name == "shared_convert") shared_convert();
    else if (name == "shared_direct") shared_direct();
    else return 2;
    std::cout << name << " passed\n";
}
