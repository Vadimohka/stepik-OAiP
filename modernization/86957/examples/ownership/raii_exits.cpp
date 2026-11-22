#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>

class Resource {
public:
    explicit Resource(std::string name) : name_{std::move(name)} {
        std::cout << "create " << name_ << '\n';
    }

    ~Resource() {
        std::cout << "destroy " << name_ << '\n';
    }

private:
    std::string name_;
};

void process(const std::string& mode) {
    Resource local{"local"};
    auto owner = std::make_unique<Resource>("dynamic");

    if (mode == "early") {
        std::cout << "early return\n";
        return;
    }
    if (mode == "throw") {
        throw std::runtime_error{"stop"};
    }
    std::cout << "normal end\n";
}

int main() {
    std::string mode;
    if (!(std::cin >> mode) ||
        (mode != "normal" && mode != "early" && mode != "throw")) {
        return 1;
    }

    try {
        process(mode);
    } catch (const std::runtime_error& error) {
        std::cout << "caught " << error.what() << '\n';
    }
    std::cout << "done\n";
}
