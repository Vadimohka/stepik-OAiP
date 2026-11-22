#include <initializer_list>
int factmod (int n, int p) {
    int res = 1;
    while (n > 1) {
        res = (res * ((n / p) % 2 ? p-1 : 1)) % p;
        for (int i = 2; i <= n % p; ++i) {
            res = (res * i) % p;
        }
        n /= p;
    }
    return res % p;
}
#include <cassert>
#include <limits>
int main() {
    static_assert(std::numeric_limits<int>::max() == 2147483647);
    for (int p : {2, 3, 46340}) {
        int answer = factmod(2000000000, p);
        assert(0 <= answer && answer < p);
    }
}
