#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>

int main() {
char* p=new char[]{"Hello"};assert(std::strcmp(p,"Hello")==0);delete[] p;

}
