#include <fstream>
#include <iostream>

int main() {
    std::ofstream out{"report.txt"};
    if (!out) {
        std::cerr << "Cannot open report.txt\n";
        return 1;
    }

    out << "count 3\n" << "sum 42\n";
    out.close();
    if (!out) {
        std::cerr << "Cannot finish report.txt\n";
        return 2;
    }
    std::cout << "saved\n";
}
