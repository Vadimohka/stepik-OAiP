#include <iostream>
int main(){int a[5]={1,2,3,4,5};for(int*p=a;p!=&a[4];++p)std::cout<<*p<<" ";}