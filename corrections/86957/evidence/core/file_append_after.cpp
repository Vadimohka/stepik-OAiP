#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
int main() {
    { std::ofstream seed("D:\\hello.txt"); seed << "Hello\n"; }
std::ofstream out("D:\\hello.txt", std::ios::app);
if (out.is_open()) {
    out << "Welcome to CPP" << std::endl;
}
out.close();        

    std::ifstream check("D:\\hello.txt");
    const std::string actual((std::istreambuf_iterator<char>(check)), {});
    return actual == "Hello\nWelcome to CPP\n" ? 0 : 1;
}
