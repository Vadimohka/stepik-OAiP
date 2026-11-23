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

    Distance operator+(const Distance& other) const {
        return add_dist(other);
    }
    Distance& operator+=(const Distance& other) {
        *this = add_dist(other);
        return *this;
    }
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
    Distance length{3, 5};
    const Distance added{11, 7};
    Distance& result = (length += added);
    std::cout << length.feet() << ' ' << length.inches() << '\n';
    std::cout << std::boolalpha << (&result == &length) << '\n';
    length += length;
    std::cout << length.feet() << ' ' << length.inches() << '\n';
    Distance limit{Distance::max_feet, 11};
    try {
        limit += Distance{0, 1};
    } catch (const std::overflow_error&) {
        std::cout << "unchanged " << limit.feet() << ' ' << limit.inches() << '\n';
    }
    return 0;
}
