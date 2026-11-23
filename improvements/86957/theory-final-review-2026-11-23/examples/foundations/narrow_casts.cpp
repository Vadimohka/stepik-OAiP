#include <iostream>
 
int main() {
    char a = 'H';
    wchar_t b = L'e';
    char16_t c = u'l';
    char32_t d = U'o';
    std::cout << a << static_cast<char>(b) << static_cast<char>(c) << static_cast<char>(d) << "\n";
    return 0;
}