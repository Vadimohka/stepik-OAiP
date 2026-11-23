#include <cstddef>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

int main() {
    std::ifstream in{"numbers.txt"};
    if (!in) {
        std::cerr << "Cannot open numbers.txt\n";
        return 1;
    }

    long long sum = 0;
    std::size_t count = 0;
    std::string token;
    while (in >> token) {
        std::istringstream field{token};
        long long value = 0;
        char extra = '\0';
        if (!(field >> value) || (field >> extra) ||
            value < -1'000'000 || value > 1'000'000) {
            std::cerr << "Invalid integer\n";
            return 2;
        }
        if (count == 1'000'000) {
            std::cerr << "Too many integers\n";
            return 3;
        }
        ++count;
        sum += value;
    }
    if (in.bad() || !in.eof()) {
        std::cerr << "Cannot read numbers.txt\n";
        return 4;
    }
    std::cout << count << ' ' << sum << '\n';
}
