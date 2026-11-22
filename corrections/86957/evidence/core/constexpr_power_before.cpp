#include <limits>
constexpr float exp(float x, int n) {
    if (n == 0)
        return 1;
    if (n % 2 == 0)
        return exp(x * x, n / 2);
    return exp(x * x, (n - 1) / 2) * x;
};
constexpr float maximum = std::numeric_limits<float>::max();
static_assert(exp(maximum, 1) == maximum);
int main() {}
