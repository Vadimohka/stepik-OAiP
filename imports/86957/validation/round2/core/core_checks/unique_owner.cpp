#include <cassert>
#include <memory>
struct Counted {
    static int alive;
    Counted() { ++alive; }
    ~Counted() { --alive; }
};
int Counted::alive = 0;
int main() {
    try {
        auto p = std::make_unique<Counted>();
        assert(Counted::alive == 1);
        throw 42;
    } catch (int) {}
    assert(Counted::alive == 0);
}
