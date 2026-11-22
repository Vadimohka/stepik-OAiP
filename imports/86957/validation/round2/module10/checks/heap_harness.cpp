#include <iostream>
#include <utility> // std::swap
using namespace std;
  
void heapify(int list[], int listLength, int root)
{
	int largest = root;
	int l = 2 * root + 1;
	int r = 2 * root + 2;
	  
	if (l < listLength && list[l] > list[largest])
		largest = l;
	  
	if (r < listLength && list[r] > list[largest])
		largest = r;

	if (largest != root) {
		swap(list[root], list[largest]);
		heapify(list, listLength, largest);
	}
}
  
void heapSort(int list[], int listLength) {
	for (int i = listLength / 2 - 1; i >= 0; i--)
		heapify(list, listLength, i);
	 
	for (int i = listLength - 1; i >= 0; i--) {
		swap(list[0], list[i]);
		heapify(list, i, 0);
	}
}
  

#include <algorithm>
#include <cassert>
#include <vector>
int main() {
    std::vector<std::vector<int>> tests{{},{1},{1,1,1},{3,2,1},{-7,2,0,2,-7},{1,2,3,4,5}};
    for (auto a : tests) {
        auto expected = a;
        std::sort(expected.begin(), expected.end());
        heapSort(a.data(), static_cast<int>(a.size()));
        assert(a == expected);
    }
}
