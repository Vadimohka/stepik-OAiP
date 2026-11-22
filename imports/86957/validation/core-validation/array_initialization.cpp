#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>

int main() {
int a[4]{}; a[0]=42; int t=a[3];
int mat[][2]={1,2,3};
static_assert(std::is_array_v<decltype(a)>);
assert(t==0 && sizeof(mat)/sizeof(int)==4 && mat[1][1]==0);

}
