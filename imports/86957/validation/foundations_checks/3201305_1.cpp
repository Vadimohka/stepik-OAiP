#include <iostream>

double InchesToMeters(double inches) {
    return 0.0254 * inches;
}

double FootsToMeters(double foots) {
    return 0.3048 * foots;
}

double MetersToInches(double meters) {
    return meters / 0.0254;
}

double MetersToFoots(double meters) {
    return meters / 0.3048;
}

int main() {
    std::cout << "Enter length: ";
    double length = 0.0;
    std::cin >> length;
    std::cout << "Inches to meters = " << InchesToMeters(length) << std::endl;
    std::cout << "Foots to meters = " << FootsToMeters(length) << std::endl;
    std::cout << "Meters to inches = " << MetersToInches(length) << std::endl;
    std::cout << "Meters to foots = " << MetersToFoots(length) << std::endl;
    std::cout << "Inches to foots = " << MetersToFoots(InchesToMeters(length)) << std::endl;
    std::cout << "Foots to inches = " << MetersToInches(FootsToMeters(length)) << std::endl;
    return 0;
}
