#include <algorithm>
#include <iostream>
#include <vector>

struct Record {
    int priority;
    int label;
};

bool by_priority(const Record& left, const Record& right) {
    return left.priority < right.priority;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    int n = 0;
    if (!(std::cin >> n) || n < 0 || n > 100000) {
        return 1;
    }
    std::vector<Record> records(static_cast<std::size_t>(n));
    for (Record& record : records) {
        if (!(std::cin >> record.priority >> record.label)) {
            return 1;
        }
    }

    std::stable_sort(records.begin(), records.end(), by_priority);

    for (const Record& record : records) {
        std::cout << record.priority << ' ' << record.label << '\n';
    }
}
