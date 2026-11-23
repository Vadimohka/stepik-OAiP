#include <iostream>

struct Sample {
    int value{};
    inline static int limit = 10;

    bool exceeds_limit() const { return value > limit; }
    static void set_limit(int next) { limit = next; }
};

int main() {
    Sample first{12}, second{8};
    std::cout << std::boolalpha << first.exceeds_limit() << ' '
              << second.exceeds_limit() << '\n';
    Sample::set_limit(7);
    std::cout << first.exceeds_limit() << ' ' << second.exceeds_limit() << '\n';
    std::cout << first.value << ' ' << second.value << '\n';
    return 0;
}
