#include <iostream>
#include <string>

typedef struct inner {
    int f;
    int g;
} inner;

typedef struct s1 {
    int x;
    int y;
    inner in;
    char* z;
} s1;

void printer(inner* inner1) {
    std::cout << inner1.f << " " << inner1.g << '\n';
}

int main() {
    s1* points = new s1[5];
    int x[3] =  {100, 200, 300};
    points[0] = {1, 1, 3, 4, new char[7]};
    points[1] = (*(s1*)(x));

    std::cout << points[0].x << " " << points[0].y << " " << points[0].in.f << " " << points[0].in.g << '\n';
    printer(&points[1].in);

    delete[] points;
    return 0;
}
