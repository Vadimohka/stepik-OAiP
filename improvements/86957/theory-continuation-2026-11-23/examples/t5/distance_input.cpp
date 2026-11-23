#include <iostream>

class Distance {
    long long feet_{};
    long long inches_{};
public:
    bool set(long long feet, long long inches) {
        if (feet < 0 || feet > 1'000'000 || inches < 0 || inches >= 12) {
            return false;
        }
        feet_ = feet;
        inches_ = inches;
        return true;
    }
    long long feet() const { return feet_; }
    long long inches() const { return inches_; }
};

int main() {
    Distance distance;
    long long feet{}, inches{};
    if (!(std::cin >> feet >> inches)) {
        std::cout << "input error\n";
        return 1;
    }
    if (!distance.set(feet, inches)) {
        std::cout << "invalid distance\n";
        return 1;
    }
    std::cout << distance.feet() << ' ' << distance.inches() << '\n';
    return 0;
}
