#include <string>

std::string s1("Hello!");
std::string s2 = "Hello!";
const char* ps = "Hello";
std::string s3(ps);
std::string s4(s3);
std::string s5;
std::string s6(1, 'A');
#include <cassert>
int main(){assert(s3=="Hello" && s6=="A");}
