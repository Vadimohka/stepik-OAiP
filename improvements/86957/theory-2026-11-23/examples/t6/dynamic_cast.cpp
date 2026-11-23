#include <iostream>
#include <typeinfo>

struct Shape {
    virtual ~Shape() = default;
};
struct Circle : Shape {
    int radius = 3;
};

int main() {
    Circle circle;
    Shape other;
    Shape* shapes[]{&circle, &other, nullptr};
    for (Shape* shape : shapes) {
        if (const auto* found = dynamic_cast<const Circle*>(shape)) {
            std::cout << found->radius << '\n';
        } else {
            std::cout << "not a circle\n";
        }
    }
    try {
        (void)dynamic_cast<Circle&>(other);
    } catch (const std::bad_cast&) {
        std::cout << "reference cast failed\n";
    }
}
