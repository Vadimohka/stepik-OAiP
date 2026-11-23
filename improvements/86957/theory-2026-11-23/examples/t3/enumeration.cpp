// Precondition: num >= 0.
int sum_of_digits(long long num) {
    int result = 0;
    do {
        result += static_cast<int>(num % 10);
        num /= 10;
    } while (num != 0);
    return result;
}

// Precondition: 0 <= interval_end <= 1'000'000'000.
long long count_by_enumeration(long long interval_end) {
    long long count = 0;
    for (long long value = 1; value <= interval_end; ++value) {
        if (sum_of_digits(value) > sum_of_digits(value + 1)) {
            ++count;
        }
    }
    return count;
}
