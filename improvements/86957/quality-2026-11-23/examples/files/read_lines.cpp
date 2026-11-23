#include <cstddef>
#include <fstream>
#include <iostream>
#include <string>

int main() {
    std::ifstream in{"names.txt"};
    if (!in) {
        std::cerr << "Cannot open names.txt\n";
        return 1;
    }

    std::string line;
    std::size_t number = 0;
    while (std::getline(in, line)) {
        std::cout << ++number << ": " << line << '\n';
    }
    if (in.bad() || !in.eof()) {
        std::cerr << "Cannot read names.txt\n";
        return 2;
    }
}
