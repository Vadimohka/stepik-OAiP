struct point_t {
    int x;
    int y;
};

typedef point_t Point; // Point и point_t — один и тот же тип

int main() {
    point_t p = {10, 20}; // C++: слово struct не требуется
    Point px = {10, 20};
    return p.x == px.x ? 0 : 1;
}
