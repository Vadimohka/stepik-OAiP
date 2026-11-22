#include <iostream>
#include <iomanip>
int main(){long double a,t,v;while(std::cin>>a>>t>>v){std::cout<<std::setprecision(20)<<(v*t+a*t*t/2)<<" | "<<((v+a*t/2)*t)<<"\n";}}
