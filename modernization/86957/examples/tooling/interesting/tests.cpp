#include "interesting.hpp"
#include <iostream>

bool Check(long long input, long long expected) {
    const long long actual = CountInterestingInInterval(input);
    if (actual == expected) {
        return true;
    }
    std::cerr << "n=" << input << ": expected " << expected
              << ", got " << actual << '\n';
    return false;
}

int main() {
    int failures = 0;
    failures += !Check(0, 0);
    failures += !Check(1, 0);
    failures += !Check(8, 0);
    failures += !Check(9, 1);
    failures += !Check(10, 1);
    failures += !Check(18, 1);
    failures += !Check(19, 2);
    failures += !Check(20, 2);
    failures += !Check(99, 10);
    failures += !Check(100, 10);
    failures += !Check(880'055'535, 88'005'553);
    failures += !Check(999'999'999, 100'000'000);
    failures += !Check(1'000'000'000, 100'000'000);
    if (failures != 0) {
        return 1;
    }
    std::cout << "13 checks passed\n";
}
