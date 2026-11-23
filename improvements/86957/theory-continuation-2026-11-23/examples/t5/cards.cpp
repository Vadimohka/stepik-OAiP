#include <array>
#include <iostream>
#include <stdexcept>
#include <utility>

enum class Suit { clubs, diamonds, hearts, spades };

class Card {
    int rank_;
    Suit suit_;
public:
    Card(int rank, Suit suit) : rank_(rank), suit_(suit) {
        if (rank < 2 || rank > 14) throw std::invalid_argument("rank");
        switch (suit) {
        case Suit::clubs: case Suit::diamonds:
        case Suit::hearts: case Suit::spades: break;
        default: throw std::invalid_argument("suit");
        }
    }
    bool same_as(const Card& other) const {
        return rank_ == other.rank_ && suit_ == other.suit_;
    }
    void print() const {
        const char* name = "";
        switch (suit_) {
        case Suit::clubs: name = "clubs"; break;
        case Suit::diamonds: name = "diamonds"; break;
        case Suit::hearts: name = "hearts"; break;
        case Suit::spades: name = "spades"; break;
        }
        std::cout << rank_ << ' ' << name << '\n';
    }
};

int main() {
    std::array<Card, 3> cards{{{7, Suit::clubs}, {11, Suit::hearts}, {14, Suit::spades}}};
    const Card selected = cards[2];
    std::swap(cards[0], cards[2]);
    std::swap(cards[1], cards[2]);
    std::swap(cards[0], cards[1]);
    for (const Card& card : cards) card.print();
    std::cout << std::boolalpha << cards[1].same_as(selected) << '\n';
    return 0;
}
