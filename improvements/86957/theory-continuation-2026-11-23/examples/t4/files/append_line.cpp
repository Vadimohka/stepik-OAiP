#include <fstream>
#include <iostream>

int main() {
    std::ofstream out{"journal.txt", std::ios::app};
    if (!out) {
        std::cerr << "Cannot open journal.txt\n";
        return 1;
    }

    out << "7\n";
    out.close();
    if (!out) {
        std::cerr << "Cannot finish journal.txt\n";
        return 2;
    }
}
