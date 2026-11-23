#include <iostream>
#include <stdexcept>
#include <string>

class Trace {
    std::string name_;
public:
    explicit Trace(const std::string& name) : name_(name) {
        std::cout << "begin " << name_ << '\n';
    }
    ~Trace() {
        std::cout << "end " << name_ << '\n';
    }
};

int main() {
    try {
        Trace first{"first"};
        Trace second{"second"};
        throw std::runtime_error("stop");
    } catch (const std::runtime_error&) {
        std::cout << "caught\n";
    }
    return 0;
}
