#include <algorithm>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

// Independent reference implementations for the revised introductory tasks.
// The validator compiles this file into a temporary directory, never the repo.
int main(int argc, char** argv) {
    if (argc < 2) return 2;
    const int step = std::stoi(argv[1]);
    if (step == 3262772) {
        double first{};
        std::cin >> first;
        std::cout << std::setprecision(argc > 2 ? std::stoi(argv[2]) : 17)
                  << first / (1.0 - 1.0 / 1001.0) << '\n';
    } else if (step == 3262735) {
        long double first{}, hundredth{};
        std::cin >> first >> hundredth;
        const long double difference = (hundredth - first) / 99.0L;
        // Sum terms explicitly, independently of the stored closed-form sum.
        long double sum = 0;
        for (int i = 0; i < 70; ++i) sum += first + i * difference;
        std::cout << std::setprecision(argc > 2 ? std::stoi(argv[2]) : 17)
                  << difference << '\n' << sum << '\n';
    } else if (step == 3264578) {
        long long x{}, y{};
        std::cin >> x >> y;
        std::cout << ((x == 0 && y == 0) ? "ERROR" :
            ((y != 0 && x % y == 0) || (x != 0 && y % x == 0)) ? "YES" : "NO");
    } else if (step == 3269060) {
        long double a[3]{};
        for (auto& x : a) std::cin >> x;
        std::sort(a, a + 3);
        std::cout << (a[0] > a[2] - a[1] ? "YES" : "NO");
    } else if (step == 3281279) {
        long double brick[3]{}, hole[2]{};
        for (auto& x : brick) std::cin >> x;
        for (auto& x : hole) std::cin >> x;
        std::sort(brick, brick + 3);
        std::sort(hole, hole + 2);
        std::cout << ((brick[0] <= 0 || hole[0] <= 0) ? "Incorrect input" :
            brick[0] <= hole[0] && brick[1] <= hole[1] ? "YES" : "NO");
    } else if (step == 3281287) {
        unsigned long long n{};
        std::cin >> n;
        const char* word = "грибов";
        if (n % 100 < 11 || n % 100 > 14) {
            if (n % 10 == 1) word = "гриб";
            else if (n % 10 >= 2 && n % 10 <= 4) word = "гриба";
        }
        std::cout << "Мы нашли " << n << ' ' << word << " в лесу\n";
    } else if (step == 3177655) {
        int k{};
        std::cin >> k;
        for (int i = 1; i < k; ++i) {
            for (int j = 1; j < k; ++j) std::cout << i * j << ' ';
            std::cout << '\n';
        }
    } else if (step == 3384444) {
        using U = unsigned long long;
        U n{};
        std::cin >> n;
        U lo = 1, hi = 3162277661ULL;
        while (lo < hi) {
            const U mid = lo + (hi - lo) / 2;
            if (mid * mid >= n) hi = mid;
            else lo = mid + 1;
        }
        const U side = lo;
        if (n <= side * side - side + 1)
            std::cout << n - (side - 1) * (side - 1) - 1 << ' ' << side - 1;
        else std::cout << side - 1 << ' ' << side * side - n;
    } else if (step == 3382745) {
        std::vector<long long> a;
        for (long long x; std::cin >> x;) a.push_back(x);
        auto min_index = std::min_element(a.begin(), a.end()) - a.begin();
        auto max_index = std::max_element(a.begin(), a.end()) - a.begin();
        if (min_index > max_index) std::swap(min_index, max_index);
        for (auto i = min_index + 1; i < max_index; ++i) a[i] = 0;
        const bool remove = 2 * std::count(a.begin(), a.end(), 0) >
                            static_cast<long long>(a.size());
        for (const auto x : a) if (!remove || x != 0) std::cout << x << ' ';
    } else if (step == 3383135) {
        int n{}, m{};
        std::cin >> n;
        std::vector<std::vector<long long>> a(n, std::vector<long long>(n));
        for (auto& row : a) for (auto& x : row) std::cin >> x;
        std::cin >> m;
        std::vector<std::vector<long long>> b(m, std::vector<long long>(m));
        for (auto& row : b) for (auto& x : row) std::cin >> x;
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < m; ++j) {
                long long sum = 0;
                for (int k = 0; k < n; ++k) sum += a[i][k] * b[k][j];
                std::cout << sum << ' ';
            }
            std::cout << '\n';
        }
    } else return 2;
}
