#include <algorithm>
#include <iostream>
#include <vector>

// A second correct solution: the original position is an explicit tie-break.
struct Record {
    int priority;
    int label;
    int original_index;
};

bool by_priority_then_index(const Record& left, const Record& right) {
    if (left.priority != right.priority) {
        return left.priority < right.priority;
    }
    return left.original_index < right.original_index;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    int n = 0;
    if (!(std::cin >> n) || n < 0 || n > 100000) {
        return 1;
    }
    std::vector<Record> records(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) {
        Record& record = records[static_cast<std::size_t>(i)];
        if (!(std::cin >> record.priority >> record.label)) {
            return 1;
        }
        record.original_index = i;
    }

    std::sort(records.begin(), records.end(), by_priority_then_index);

    for (const Record& record : records) {
        std::cout << record.priority << ' ' << record.label << '\n';
    }
}
