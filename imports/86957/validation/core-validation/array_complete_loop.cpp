#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>

int main() {
int a[5] = { 1, 2, 3, 4, 5 };
 
for (int *ptr=a; ptr != a + 5; ptr++) {
    std::cout << "address=" << ptr << "\tvalue=" << *ptr << std::endl;
}

}
