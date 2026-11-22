#include <cassert>
#include <limits>
#include <type_traits>
static_assert(std::is_same_v<decltype('a'), char>);
static_assert(std::is_same_v<decltype(42), int>);
static_assert(std::is_same_v<decltype(1234567890L), long>);
static_assert(std::is_same_v<decltype(1703U), unsigned int>);
static_assert(std::is_same_v<decltype(2128506UL), unsigned long>);
static_assert(std::is_same_v<decltype(3.14), double>);
static_assert(std::is_same_v<decltype(!0x0), bool>);
static_assert(std::is_same_v<decltype(false & true), int>);
static_assert(std::is_same_v<decltype(false && true), bool>);
int main() {
    assert(14/3 == 4 && !0x0);
    assert(!(false & true) && !(false && true));
    assert((2 << 2) == 8 && (16 >> 3) == 2 && ~9 == -10);
    for (int state=0; state<4; ++state) {
        const int online=1, offline=2;
        int status=state;
        status |= online;
        assert((status & online) && ((status & offline) == (state & offline)));
        status = online;
        if (state & offline) assert((status & offline) != (state & offline));
    }
    static_assert(std::numeric_limits<double>::radix == 2);
    static_assert(std::numeric_limits<double>::digits == 53);
    long long integer=9007199254740993LL;
    double rounded=static_cast<double>(integer);
    assert(static_cast<long long>(rounded) != integer);
}
