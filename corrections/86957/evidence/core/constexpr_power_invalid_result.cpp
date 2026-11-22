#include <limits>
constexpr float exp(float x, int n) {
    if (n == 0)
        return 1;
    if (n == 1)
        return x;
    if (n % 2 == 0)
        return exp(x * x, n / 2);
    return exp(x * x, (n - 1) / 2) * x;
};
constexpr float overflow = exp(std::numeric_limits<float>::max(), 2);
int main() {}
