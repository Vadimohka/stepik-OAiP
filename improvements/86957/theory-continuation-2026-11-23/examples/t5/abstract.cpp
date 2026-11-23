#include <array>
#include <iostream>
#include <stdexcept>

class Shape {
public:
    virtual long long area() const = 0;
    virtual ~Shape() = default;
};

class Rectangle : public Shape {
    long long width_;
    long long height_;
public:
    Rectangle(long long width, long long height) : width_(width), height_(height) {
        if (width < 0 || width > 1'000'000 || height < 0 || height > 1'000'000) {
            throw std::invalid_argument("rectangle");
        }
    }
    long long area() const override { return width_ * height_; }
};

class UnitSquare : public Shape {
public:
    long long area() const override { return 1; }
};

int main() {
    const Rectangle rectangle{3, 4};
    const UnitSquare square;
    std::array<const Shape*, 2> shapes{{&rectangle, &square}};
    for (const Shape* shape : shapes) {
        std::cout << shape->area() << '\n';
    }
    return 0;
}
