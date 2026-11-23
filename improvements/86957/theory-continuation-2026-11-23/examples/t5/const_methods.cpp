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
    Distance add_dist(const Distance& other) const {
        const long long total = total_inches() + other.total_inches();
        if (total > max_feet * 12 + 11) {
            throw std::overflow_error("distance sum");
        }
        return Distance{total / 12, total % 12};
    }
};

int main() {
    const Distance first{1, 6};
    const Distance second{0, 8};
    Distance sum = first.add_dist(second);
    std::cout << sum.feet() << ' ' << sum.inches() << '\n';
    std::cout << first.total_inches() << ' ' << second.total_inches() << '\n';
    return 0;
}
