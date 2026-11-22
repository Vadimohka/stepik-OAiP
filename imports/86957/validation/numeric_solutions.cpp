// Independent bounded C++17 reference solutions for the revised numeric tasks.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const std::string task = argv[1];
    std::cout << std::setprecision(25);
    if (task == "3262682") {
        long double h;
        std::cin >> h;
        std::cout << std::sqrt(2 * h / 9.8L);
    } else if (task == "3262692") {
        long double a, t, v;
        std::cin >> a >> t >> v;
        // Deliberately factor the expression to exercise different rounding.
        std::cout << (v + a * t / 2) * t;
    } else if (task == "3264622") {
        long double k, x, y;
        std::cin >> k >> x >> y;
        const auto lo = std::min(0.0L, k), hi = std::max(0.0L, k);
        const auto cx = std::clamp(x, lo, hi), cy = std::clamp(y, lo, hi);
        // Distance to each of the four closed segments, including endpoints.
        std::cout << std::min({std::hypot(x - lo, y - cy), std::hypot(x - hi, y - cy),
                               std::hypot(x - cx, y - lo), std::hypot(x - cx, y - hi)});
    } else if (task == "3280697") {
        long long x, y;
        std::array<long double, 3> values{};
        long double k;
        std::cin >> x >> y >> values[0] >> values[1] >> values[2] >> k;
        if (x == y) x = y = 0;
        else if (x < y) x = 0;
        else y = 0;
        // max_element chooses the first maximum without changing the others.
        *std::max_element(values.begin(), values.end()) -= k;
        std::cout << x << ' ' << y << '\n';
        for (auto value : values) std::cout << value << ' ';
    } else if (task == "3280727") {
        long double a, b, c, d;
        std::cin >> a >> b >> c >> d;
        if (c >= d && a < d) {
            if (c == 0) std::cout << "ERROR";
            else std::cout << a + b / c;
        } else if (c < d && a >= d) {
            if (c == 0) std::cout << "ERROR";
            else std::cout << a - b / c;
        } else {
            std::cout << 0;
        }
    } else if (task == "3281353") {
        long long width, height, x1, y1, x2, y2, w, h;
        std::cin >> width >> height >> x1 >> y1 >> x2 >> y2 >> w >> h;
        auto result = std::numeric_limits<long long>::max();
        if (x2 - x1 + w <= width && h <= height) {
            result = std::min(std::max(0LL, w - x1), std::max(0LL, w - (width - x2)));
        }
        if (y2 - y1 + h <= height && w <= width) {
            result = std::min(result, std::min(std::max(0LL, h - y1), std::max(0LL, h - (height - y2))));
        }
        std::cout << (result == std::numeric_limits<long long>::max() ? -1 : result);
    } else {
        return 2;
    }
    std::cout << '\n';
}
