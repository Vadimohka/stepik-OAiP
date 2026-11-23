#include <iostream>

struct Point {
    int x{};
    int y{};
};
using Position = Point;

int main() {
    Point p{10, 20};
    Position q = p;
    q.x = 30;
    std::cout << p.x << ' ' << q.x << '\n';
    return 0;
}
