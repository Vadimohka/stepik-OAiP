#include <cassert>
#include <iostream>
#include <string>
#include <cstring>
#include <type_traits>
#include <climits>
int SearchingAlgorithm(const int arr[], int left, int right, int key) {
    // Непустой диапазон должен находиться в границах отсортированного массива.
    while (left <= right) {
        int middle = left + (right - left) / 2;
        if (key < arr[middle]) {
            right = middle - 1;
        } else if (key > arr[middle]) {
            left = middle + 1;
        } else {
            return middle;
        }
    }
    return -1;
}
int main(){int a[]{1,2,3,4,5,6,7,8,9,10};assert(SearchingAlgorithm(a,0,9,2)==1);assert(SearchingAlgorithm(a,0,9,1)==0);assert(SearchingAlgorithm(a,0,9,10)==9);assert(SearchingAlgorithm(a,0,9,11)==-1);assert(SearchingAlgorithm(nullptr,0,-1,1)==-1);}
