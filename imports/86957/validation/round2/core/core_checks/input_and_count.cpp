#include <climits>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

int GetNumber(int intervalBegin, int intervalEnd, std::string purpose);
int CountInterestingInInterval(int intervalEnd);
void WriteEmptyLine(int n = 1);

int main() {
    try {
        WriteEmptyLine();
        int t = GetNumber(1, 1000, "count of calculations");
        WriteEmptyLine();
        for (int i = 0; i < t; ++i) {
            int n = GetNumber(1, 1'000'000'000, "end of the interval N" + std::to_string(i + 1));
            std::cout << "  Answer : " << CountInterestingInInterval(n) << "\n\n";
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}

int GetNumber(int intervalBegin = INT_MIN, int intervalEnd = INT_MAX, std::string purpose = "number") {
    while (true) {
        int value;
        std::cout << "  Enter " << purpose << " : ";
        if (std::cin >> value) {
            if (value >= intervalBegin && value <= intervalEnd) {
                return value;
            }
        } else if (std::cin.eof() || std::cin.bad()) {
            throw std::runtime_error("Input ended or cannot be read");
        }
        std::cin.clear();
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        std::cout << "  Input Error. Please repeat\n\n";
    }
}

int CountInterestingInInterval(int intervalEnd) {
    return (intervalEnd + 1) / 10;
}

void WriteEmptyLine(int n) {
    for (int i = 0; i < n; ++i) {
        std::cout << '\n';
    }
}
