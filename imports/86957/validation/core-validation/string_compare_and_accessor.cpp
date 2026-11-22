#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>
int main(){std::string s="default";assert(!(s!="default"));s="x";assert(s!="default");static_assert(std::is_same_v<decltype(s.c_str()),const char*>);assert(std::strcmp("a","b")<0);assert(std::strcmp("a","a")==0);assert(std::strcmp("b","a")>0);static_assert(std::is_same_v<decltype('a'),char>);}
