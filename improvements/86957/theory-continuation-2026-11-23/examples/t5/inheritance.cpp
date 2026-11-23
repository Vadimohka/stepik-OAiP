#include <iostream>
#include <string>

class Device {
    std::string name_;
public:
    explicit Device(const std::string& name) : name_(name) {}
    const std::string& name() const { return name_; }
};

class Printer : public Device {
    int pages_per_minute_;
public:
    Printer(const std::string& name, int speed)
        : Device(name), pages_per_minute_(speed) {}
    int speed() const { return pages_per_minute_; }
};

void print_name(const Device& device) {
    std::cout << device.name() << '\n';
}

int main() {
    const Printer printer{"Office", 20};
    print_name(printer);
    std::cout << printer.speed() << '\n';
    return 0;
}
