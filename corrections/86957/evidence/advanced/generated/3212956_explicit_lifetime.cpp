
#include <new>
#include <string>
union U { int i; std::string s; U():i(1){} ~U(){} };
int main() { U u; new (&u.s) std::string("ok");
    if(u.s != "ok") return 1; u.s.~basic_string(); u.i = 7;
    return u.i == 7 ? 0 : 2; }
