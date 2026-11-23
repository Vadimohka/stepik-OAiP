#include <iostream>
#include <queue>
#include <string>

int main() {
    std::queue<std::string> pending;
    pending.push("parse");
    pending.push("save");
    while (!pending.empty()) {
        std::string current = pending.front();
        pending.pop();
        std::cout << current << '\n';
    }
}
