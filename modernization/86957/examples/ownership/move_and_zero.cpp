#include <iostream>
#include <string>
#include <utility>
#include <vector>

struct Group {
    std::string name;
    std::vector<int> scores;
};

int main() {
    Group source{"A", {4, 5}};
    Group copy = source;
    copy.scores[0] = 1;

    Group destination = std::move(source);
    std::cout << copy.scores[0] << ' ' << destination.scores[0] << '\n';
    std::cout << destination.name << ' ' << destination.scores.size() << '\n';

    source = Group{"B", {3}};
    std::cout << source.name << ' ' << source.scores[0] << '\n';
}
