#include <iostream>
#include <cmath>
int sum(int n){int r=0;for(int i=0;std::pow(10,i)<n;++i)r+=(int)(n/std::pow(10,i))%10;return r;}
int main(){std::cout<<sum(1)<<" "<<sum(10)<<" "<<sum(100);}