#include <iostream>

struct Ticket {
    int number;
    explicit Ticket(int value) : number{value} {}
    Ticket(const Ticket&) = delete;
    Ticket(Ticket&&) = delete;
};

Ticket make_ticket() {
    return Ticket{42};
}

int main() {
    Ticket ticket = make_ticket();
    std::cout << ticket.number << '\n';
}
