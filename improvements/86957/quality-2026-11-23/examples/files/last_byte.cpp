#include <fstream>
#include <iostream>

int main() {
    std::ifstream in{"letters.bin", std::ios::binary};
    if (!in) {
        std::cerr << "Cannot open letters.bin\n";
        return 1;
    }

    in.seekg(-1, std::ios::end);
    if (!in) {
        std::cerr << "Cannot seek letters.bin\n";
        return 2;
    }
    char last = '\0';
    if (!in.get(last)) {
        std::cerr << "Cannot read letters.bin\n";
        return 3;
    }
    std::cout << last << '\n';
}
