#include <iostream>
#include <vector>
int main() {
    int outer{7};
    {
        std::vector<int> values{10, 20, 30};
        int* element = &values[1];
        *element = 21;
        std::cout << values[1] << '\n';
    }
    std::cout << outer << '\n';
}
