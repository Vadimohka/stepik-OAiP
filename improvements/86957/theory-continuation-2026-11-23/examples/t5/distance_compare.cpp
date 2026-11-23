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
    bool operator<(const Distance& other) const {
        return feet_ < other.feet_ ||
               (feet_ == other.feet_ && inches_ < other.inches_);
    }
    bool operator==(const Distance& other) const {
        return feet_ == other.feet_ && inches_ == other.inches_;
    }
    bool operator!=(const Distance& other) const {
        return !(*this == other);
    }
};

int main() {
    const Distance first{5, 11};
    const Distance second{6, 0};
    const Distance equal{5, 11};
    std::cout << std::boolalpha << (first < second) << ' '
              << (second < first) << '\n';
    std::cout << (first == equal) << ' ' << (first != equal) << '\n';
    return 0;
}
