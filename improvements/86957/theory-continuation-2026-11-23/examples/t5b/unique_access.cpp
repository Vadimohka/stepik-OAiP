#include <iostream>
#include <memory>
#include <utility>

struct Record {
    int score{0};
};

void print_score(const Record& record) {
    std::cout << record.score << '\n';
}

int main() {
    Record local{10};
    print_score(local);

    auto first = std::make_unique<Record>();
    first->score = 42;
    Record* observer = first.get();
    print_score(*first);

    auto second = std::move(first);
    std::cout << std::boolalpha << static_cast<bool>(first) << ' '
              << static_cast<bool>(second) << '\n';
    print_score(*observer);

    second.reset();
    observer = nullptr;
    std::cout << static_cast<bool>(second) << '\n';
}
