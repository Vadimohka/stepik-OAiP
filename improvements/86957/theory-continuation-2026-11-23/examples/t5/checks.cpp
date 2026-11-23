// Author verification only. This is not a learner task or a new Stepik step.
#include "distance.hpp"
#include "counter.hpp"
#include <cassert>
#include <limits>
#include <type_traits>
#include <utility>

#define main level_example_main
#include "level.cpp"
#undef main
#define main cards_example_main
#include "cards.cpp"
#undef main
#define main array_example_main
#include "checked_array.cpp"
#undef main
#define main abstract_example_main
#include "abstract.cpp"
#undef main

template<class Error, class Operation>
void must_throw(Operation operation) {
    bool seen = false;
    try { operation(); } catch (const Error&) { seen = true; }
    assert(seen);
}

int main() {
    static_assert(std::is_same_v<decltype(++std::declval<Counter&>()), Counter&>);
    static_assert(std::is_same_v<decltype(std::declval<Counter&>()++), Counter>);
    static_assert(std::is_same_v<decltype(std::declval<Distance&>() += std::declval<const Distance&>()), Distance&>);
    static_assert(std::is_same_v<decltype(std::declval<CheckedArray&>()[0]), int&>);
    static_assert(std::is_same_v<decltype(std::declval<const CheckedArray&>()[0]), const int&>);
    static_assert(std::is_abstract_v<Shape> && std::has_virtual_destructor_v<Shape>);

    const Distance zero;
    const Distance limit{Distance::max_feet, 11};
    assert(zero.total_inches() == 0);
    assert((zero + limit) == limit && (limit + zero) == limit);
    assert((Distance{0, 11} + Distance{0, 1}) == Distance(1, 0));
    must_throw<std::invalid_argument>([] { (void)Distance{-1, 0}; });
    must_throw<std::invalid_argument>([] { (void)Distance{0, -1}; });
    must_throw<std::invalid_argument>([] { (void)Distance{0, 12}; });
    must_throw<std::invalid_argument>([] { (void)Distance{Distance::max_feet + 1, 0}; });
    must_throw<std::invalid_argument>([] { (void)Distance{std::numeric_limits<long long>::max(), 0}; });
    must_throw<std::invalid_argument>([] { (void)Distance{0, std::numeric_limits<long long>::max()}; });
    Distance mutable_limit = limit;
    must_throw<std::overflow_error>([&] { mutable_limit += Distance{0, 1}; });
    assert(mutable_limit == limit);
    must_throw<std::overflow_error>([&] { mutable_limit += mutable_limit; });
    assert(mutable_limit == limit);
    Distance self{4, 7};
    assert(&(self += self) == &self);
    assert(self == Distance(9, 2));
    for (long long a = 0; a < 36; ++a) {
        const Distance left{a / 12, a % 12};
        assert(!(left < left));
        for (long long b = 0; b < 36; ++b) {
            const Distance right{b / 12, b % 12};
            assert((left < right) == (a < b));
            assert((left == right) == (a == b));
            assert((left != right) == (a != b));
        }
    }

    Counter counter;
    assert(&(++counter) == &counter && counter.value() == 1);
    const Counter old = counter++;
    assert(old.value() == 1 && counter.value() == 2);
    Counter maximum{std::numeric_limits<unsigned>::max()};
    must_throw<std::overflow_error>([&] { ++maximum; });
    assert(maximum.value() == std::numeric_limits<unsigned>::max());
    must_throw<std::overflow_error>([&] { (void)maximum++; });
    assert(maximum.value() == std::numeric_limits<unsigned>::max());

    Level level;
    assert(level.value() == 0 && level.set(100) && level.value() == 100);
    assert(!level.set(101) && !level.set(-1) && level.value() == 100);
    assert(level.set(0) && level.value() == 0);

    const Card lowest{2, Suit::clubs};
    const Card highest{14, Suit::spades};
    assert(!lowest.same_as(highest));
    const Card duplicate = highest;
    assert(duplicate.same_as(highest));
    must_throw<std::invalid_argument>([] { (void)Card{1, Suit::clubs}; });
    must_throw<std::invalid_argument>([] { (void)Card{15, Suit::clubs}; });
    must_throw<std::invalid_argument>([] { (void)Card{2, static_cast<Suit>(99)}; });

    CheckedArray array;
    for (std::size_t i = 0; i < 4; ++i) assert(array[i] == 0);
    array[0] = 7; array[3] = 11;
    const CheckedArray& const_array = array;
    assert(const_array[0] == 7 && const_array[3] == 11);
    must_throw<std::out_of_range>([&] { array[4] = 99; });
    must_throw<std::out_of_range>([&] { (void)const_array[static_cast<std::size_t>(-1)]; });
    assert(array[0] == 7 && array[3] == 11);

    assert(Rectangle(0, 0).area() == 0);
    assert(Rectangle(1'000'000, 1'000'000).area() == 1'000'000'000'000LL);
    must_throw<std::invalid_argument>([] { (void)Rectangle{-1, 0}; });
    must_throw<std::invalid_argument>([] { (void)Rectangle{0, 1'000'001}; });
    struct Tracked : Shape {
        bool* destroyed;
        explicit Tracked(bool& state) : destroyed(&state) {}
        ~Tracked() override { *destroyed = true; }
        long long area() const override { return 0; }
    };
    bool destroyed = false;
    Shape* owned = new Tracked(destroyed);
    delete owned;
    assert(destroyed);

    // The nested trivial union fragment begins only the members it subsequently reads.
    union Number { int integer; double real; };
    union Payload { Number number; int code; };
    Payload payload{{5}};
    assert(payload.number.integer == 5);
    payload.number.real = 2.5;
    assert(payload.number.real == 2.5);
    payload.code = 9;
    assert(payload.code == 9);

    std::cout << "T5 boundaries passed\n";
    return 0;
}
