#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>

int main() {
int values[]{10, 23, 42};
int* first = values;
int* last = values + 2;
auto distance = last - first; // 2
std::cout << distance;
assert(distance==2);
}
