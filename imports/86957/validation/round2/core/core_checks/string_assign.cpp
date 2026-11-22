#include <string>
#include <cassert>
int main() {

// тип string
std::string s1; // переменная с именем s1 типа string
std::string s2 = "This is a string variable"; // объявление с инициализацией
// использование переменной типа string с оператором присваивания
s1 = s2; // s1 = "This is a string variable"
s2 = "New text";
assert(s1 == "This is a string variable"); assert(s2 == "New text");
}
