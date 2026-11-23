#include <iostream>
#include <iterator> // std::size, начиная с C++17
using namespace std;

int main() {
    int a[] {1,2,3,4,5};
    cout << size(a);
    return 0;
}