#include <iostream>

class Counter {
    unsigned count_;
public:
    explicit Counter(unsigned initial) : count_(initial) {}
    unsigned value() const { return count_; }
};

Counter make_counter(unsigned initial) {
    return Counter{initial};
}

int main() {
    Counter first = make_counter(3);
    const Counter& temporary = Counter{7};
    std::cout << first.value() << ' ' << temporary.value() << '\n';
    return 0;
}
