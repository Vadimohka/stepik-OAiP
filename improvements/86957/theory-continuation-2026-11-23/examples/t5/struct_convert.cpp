#include <iostream>

struct Point { int x; int y; };
struct Apex { int a; int b; };

int main() {
    Point point{10, 20};
    Apex apex{point.x, point.y};
    std::cout << apex.a << ' ' << apex.b << '\n';
    return 0;
}
