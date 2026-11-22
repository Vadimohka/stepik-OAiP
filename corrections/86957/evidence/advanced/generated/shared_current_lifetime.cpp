#include <cstddef>
#include <utility>

namespace teaching {

template<class T>
struct control_block {
    T* value;
    std::size_t strong;
    std::size_t weak;
};

template<class T> class weak_ptr;

template<class T>
class shared_ptr {
    control_block<T>* control_ = nullptr;
    struct counted_t {};
    shared_ptr(control_block<T>* p, counted_t) noexcept : control_(p) {}
    friend class weak_ptr<T>;

    void release() noexcept {
        if (control_ && --control_->strong == 0) {
            T* value = std::exchange(control_->value, nullptr);
            delete value; // служебная слабая ссылка удерживает блок
            if (--control_->weak == 0) delete control_;
        }
        control_ = nullptr;
    }

public:
    shared_ptr() noexcept = default;

    explicit shared_ptr(T* p) {
        if (!p) return;
        try {
            control_ = new control_block<T>{p, 1, 1};
        } catch (...) {
            delete p;
            throw;
        }
    }

    shared_ptr(const shared_ptr& other) noexcept : control_(other.control_) {
        if (control_) ++control_->strong;
    }
    shared_ptr(shared_ptr&& other) noexcept
        : control_(std::exchange(other.control_, nullptr)) {}
    shared_ptr& operator=(shared_ptr other) noexcept {
        swap(other);
        return *this;
    }
    ~shared_ptr() { release(); }

    void swap(shared_ptr& other) noexcept { std::swap(control_, other.control_); }
    void reset() noexcept { shared_ptr{}.swap(*this); }
    std::size_t use_count() const noexcept { return control_ ? control_->strong : 0; }
    T* get() const noexcept { return control_ ? control_->value : nullptr; }
    explicit operator bool() const noexcept { return get() != nullptr; }
    T& operator*() const { return *get(); } // только для непустого указателя
    T* operator->() const noexcept { return get(); }
};

template<class T>
class weak_ptr {
    control_block<T>* control_ = nullptr;

    void release() noexcept {
        if (control_ && --control_->weak == 0) {
            delete control_;
        }
        control_ = nullptr;
    }

public:
    weak_ptr() noexcept = default;
    weak_ptr(const shared_ptr<T>& owner) noexcept : control_(owner.control_) {
        if (control_) ++control_->weak;
    }
    weak_ptr(const weak_ptr& other) noexcept : control_(other.control_) {
        if (control_) ++control_->weak;
    }
    weak_ptr(weak_ptr&& other) noexcept
        : control_(std::exchange(other.control_, nullptr)) {}
    weak_ptr& operator=(weak_ptr other) noexcept {
        swap(other);
        return *this;
    }
    ~weak_ptr() { release(); }

    void swap(weak_ptr& other) noexcept { std::swap(control_, other.control_); }
    void reset() noexcept { weak_ptr{}.swap(*this); }
    std::size_t use_count() const noexcept { return control_ ? control_->strong : 0; }
    bool expired() const noexcept { return use_count() == 0; }

    shared_ptr<T> lock() const noexcept {
        if (!control_ || control_->strong == 0) return {};
        ++control_->strong;
        return shared_ptr<T>(control_, typename shared_ptr<T>::counted_t{});
    }

    bool same_owner(const weak_ptr& other) const noexcept {
        return control_ == other.control_;
    }
};

} // namespace teaching
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
