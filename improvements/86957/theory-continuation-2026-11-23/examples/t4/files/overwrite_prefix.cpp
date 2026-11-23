#include <fstream>
#include <iostream>

int main() {
    std::fstream file{"text.txt"};
    if (!file) {
        std::cerr << "Cannot open text.txt\n";
        return 1;
    }

    file << "LUCI";
    file.close();
    if (!file) {
        std::cerr << "Cannot finish text.txt\n";
        return 2;
    }
}
