#include <iostream>
#include <memory>

int main() {
    auto owner = std::make_shared<int>(42);
    std::weak_ptr<int> observer = owner;
    {
        auto second = owner;
        std::cout << owner.use_count() << '\n';
    }
    std::cout << owner.use_count() << '\n';

    auto held = observer.lock();
    if (held) {
        std::cout << *held << '\n';
    }
    owner.reset();
    std::cout << std::boolalpha << observer.expired() << ' '
              << static_cast<bool>(held) << '\n';
    held.reset();
    auto result = observer.lock();
    std::cout << observer.expired() << ' '
              << static_cast<bool>(result) << '\n';
}
