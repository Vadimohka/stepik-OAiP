// cardobj.cpp
// игральные карты в качестве объектов
#include <iostream>

enum Suit {
    clubs, diamonds, hearts, spades
};
const int jack = 11; // именованные достоинства карт
const int queen = 12;
const int king = 13;
const int ace = 14;


class card {
private:
    int number; // достоинство карты
    Suit suit; // масть

public:
    // конструктор без аргументов
    card() {}

    // конструктор с двумя аргументами
    card(int n, Suit s) {
        number = n;
        suit = s;
    }

    void display(); // вывод карты на экран
    bool isEqual(card); // результат сравнения карт
};

// вывод карты на экран
void card::display()  {
    if (number >= 2 && number <= 10) {
        std::cout << number << " ";
    }
    else {
        switch (number) {
        case jack:
            std::cout << "Валет ";
            break;
        case queen:
            std::cout << "Дама ";
            break;
        case king:
            std::cout << "Король ";
            break;
        case ace:
            std::cout << "Туз ";
            break;
        }
    }

    switch (suit) {
    case clubs:
        std::cout << "треф";
        break;
    case diamonds:
        std::cout << "бубен";
        break;
    case hearts:
        std::cout << "червей";
        break;
    case spades:
        std::cout << "пик";
        break;
    }
}

// сравнение двух карт
bool card::isEqual(card c2) {
    return (number == c2.number && suit == c2.suit);
}


int main() {
    setlocale(LC_ALL, "Russian");
    card temp, chosen, prize; // 3 карты
    int position;
    card card1(7, clubs); // определение и инициализация card1
    std::cout << "Карта 1: ";
    card1.display(); // вывод card1
    card card2(jack, hearts); // определение и инициализация card2
    std::cout << "\nКарта 2: ";
    card2.display(); // вывод card2
    card card3(ace, spades); // определение и инициализация card3
    std::cout << "\nКарта 3: ";
    card3.display(); // вывод card3
    prize = card3; // карту prize будет необходимо угадать
    std::cout << "\nМеняем местами карты 1 и 3...";
    temp = card3;
    card3 = card1;
    card1 = temp;
    std::cout << "\nМеняем местами карты 2 и 3...";
    temp = card3;
    card3 = card2;
    card2 = temp;
    std::cout << "\nМеняем местами карты 1 и 2...";
    temp = card2;
    card2 = card1;
    card1 = temp;
    std::cout << "\nНа какой позиции (1, 2 или 3) теперь ";
    prize.display(); // угадываемая карта
    std::cout << "? ";
    std::cin >> position; // ввод позиции игроком
    // chosen - карта на позиции,
    switch (position) { 
    case 1:
        chosen = card1;
        break; // выбранной игроком
    case 2:
        chosen = card2;
        break;
    case 3:
        chosen = card3;
        break;
    }
    // сравнение карт
    if (chosen.isEqual(prize)) {
        std::cout << "Правильно! Вы выиграли! ";
    }
    else {
        std::cout << "Неверно. Вы проиграли. Вы выбрали карту ";
        chosen.display(); // вывод выбранной карты
    }
    std::cout << std::endl;
    return 0;
}