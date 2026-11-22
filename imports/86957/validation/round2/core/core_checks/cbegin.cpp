#include <iterator>
int main() { int a[2]{}; const int* p = std::cbegin(a); return *p; }
