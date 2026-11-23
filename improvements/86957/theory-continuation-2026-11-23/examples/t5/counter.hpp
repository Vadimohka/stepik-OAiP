#pragma once
#include <limits>
#include <stdexcept>

class Counter {
    unsigned count_{};
public:
    Counter() = default;
    explicit Counter(unsigned initial) : count_(initial) {}
    unsigned value() const { return count_; }

    Counter& operator++() {
        if (count_ == std::numeric_limits<unsigned>::max()) {
            throw std::overflow_error("counter");
        }
        ++count_;
        return *this;
    }

    Counter operator++(int) {
        Counter old = *this;
        ++(*this);
        return old;
    }
};
