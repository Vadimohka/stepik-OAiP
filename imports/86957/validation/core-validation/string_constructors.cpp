#include <cstddef>
#include <string>

std::string S = "abcdef";
std::size_t n = 3, start = 1, len = 2;
char c = 'x';

std::string empty;                // пустая строка
std::string copy(S);              // "abcdef"
std::string repeated(n, c);       // "xxx"
std::string one_character(1, c);  // "x"
std::string part(S, start, len);  // "bc"
#include <cassert>
int main(){assert(empty.empty() && copy=="abcdef" && repeated=="xxx" && one_character=="x" && part=="bc");}
