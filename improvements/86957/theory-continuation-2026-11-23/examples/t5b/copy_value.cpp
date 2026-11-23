#include <iostream>
#include <vector>

struct Record {
    std::vector<int> scores;
};

int main() {
    Record source{{4, 5}};
    Record copy = source;
    copy.scores[0] = 1;

    Record assigned{{9}};
    assigned = source;
    assigned.scores.push_back(6);

    std::cout << source.scores[0] << ' ' << copy.scores[0] << '\n';
    std::cout << source.scores.size() << ' ' << assigned.scores.size() << '\n';
}
