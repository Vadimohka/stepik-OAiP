#include <iostream>

class Level {
    int value_{};
public:
    int value() const { return value_; }
    bool set(int next) {
        if (next < 0 || next > 100) return false;
        value_ = next;
        return true;
    }
};

int main() {
    Level level;
    std::cout << level.value() << '\n';
    std::cout << std::boolalpha << level.set(70) << ' ' << level.value() << '\n';
    std::cout << level.set(150) << ' ' << level.value() << '\n';
    return 0;
}
