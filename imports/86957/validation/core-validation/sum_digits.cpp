#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>
int SumOfDigits(int num) {
    // Предусловие: num >= 0.
    int result = 0;
    do {
        result += num % 10;
        num /= 10;
    } while (num != 0);
    return result;
}

int CountInterestingInInterval(int intervalEnd) {
    int result = 0;
    for (int i = 1; i <= intervalEnd; ++i) {
        if (SumOfDigits(i) > SumOfDigits(i + 1)) {
            ++result;
        }
    }
    return result;
}
int main(){assert(SumOfDigits(0)==0);assert(SumOfDigits(1)==1);assert(SumOfDigits(10)==1);assert(SumOfDigits(100)==1);assert(SumOfDigits(999)==27);assert(CountInterestingInInterval(1000)==100);}
