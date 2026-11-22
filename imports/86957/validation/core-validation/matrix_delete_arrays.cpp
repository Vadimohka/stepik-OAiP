#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>

int main() {
int** mat = new int*[2];
for (int i = 0; i < 2; ++i) {
    mat[i] = new int[3]{};
}
for (int i = 0; i < 2; ++i) {
    delete[] mat[i];
    mat[i] = nullptr;
}
delete[] mat;
mat = nullptr;

}
