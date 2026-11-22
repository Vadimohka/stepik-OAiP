#include <limits>
#include <initializer_list>
constexpr float exp(float x, int n) {
    if (n == 0)
        return 1;
    if (n == 1)
        return x;
    if (n % 2 == 0)
        return exp(x * x, n / 2);
    return exp(x * x, (n - 1) / 2) * x;
};
constexpr float maximum = std::numeric_limits<float>::max();
static_assert(exp(maximum, 0) == 1);
static_assert(exp(maximum, 1) == maximum);
static_assert(exp(-maximum, 1) == -maximum);
static_assert(exp(2.0f, 127) == 0x1p127f);
static_assert(exp(-2.0f, 127) == -0x1p127f);
static_assert(exp(0.0f, 0) == 1);
static_assert(exp(0.0f, 5) == 0);
static_assert(exp(2.0f, 10) == 1024);
static_assert(exp(-2.0f, 9) == -512);
static_assert(exp(0.5f, 3) == 0.125f);
int main() {
    for (float base : {-2.0f, -1.0f, 0.0f, 0.5f, 1.0f, 2.0f}) {
        float expected = 1.0f;
        for (int n=0; n<=20; ++n) {
            if (exp(base,n) != expected) return 1;
            expected *= base;
        }
    }
}
