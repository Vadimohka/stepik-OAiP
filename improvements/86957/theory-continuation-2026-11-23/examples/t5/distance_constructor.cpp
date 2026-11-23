#include <iostream>
#include <stdexcept>

class Distance {
    long long feet_{};
    long long inches_{};
public:
    static constexpr long long max_feet = 1'000'000;

    Distance() = default;
    Distance(long long feet, long long inches)
        : feet_(feet), inches_(inches) {
        if (feet < 0 || feet > max_feet || inches < 0 || inches >= 12) {
            throw std::invalid_argument("distance");
        }
    }

    long long feet() const { return feet_; }
    long long inches() const { return inches_; }
    long long total_inches() const { return feet_ * 12 + inches_; }
};

int main() {
    Distance zero;
    const Distance length{11, 6};
    std::cout << zero.feet() << ' ' << zero.inches() << '\n';
    std::cout << length.total_inches() << '\n';
    try {
        Distance invalid{1, 12};
        std::cout << invalid.total_inches() << '\n';
    } catch (const std::invalid_argument&) {
        std::cout << "invalid distance\n";
    }
    return 0;
}
