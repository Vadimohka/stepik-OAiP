#include "factorial.hpp"

unsigned long long factorial(unsigned int n) {
    unsigned long long result = 1;
    for (unsigned int factor = 2; factor <= n; ++factor) {
        result *= factor;
    }
    return result;
}
