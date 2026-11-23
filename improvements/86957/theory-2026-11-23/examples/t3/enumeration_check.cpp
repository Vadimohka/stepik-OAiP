#include "interesting.hpp"
long long count_by_enumeration(long long);
int main() {
    for (long long n = 0; n <= 1000; ++n) {
        if (count_by_enumeration(n) != CountInterestingInInterval(n)) return 1;
    }
}
