#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>

int main() {
double values[]{10.6, 20.6, 30.6, 40.6};
double* pd = values;
pd += 2;              // &values[2]
std::cout << *pd;     // 30.6
pd -= 1;              // &values[1]

char letters[]{'A', 'B', 'C', 'D'};
char* pc = &letters[3];
pc -= 3;              // &letters[0]
std::cout << *pc;     // A
assert(pd==values+1 && pc==letters);
}
