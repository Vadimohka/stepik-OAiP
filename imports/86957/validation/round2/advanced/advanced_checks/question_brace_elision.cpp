#include <cassert>
struct inner {int f;int g;};
struct s1 {int x;int y;inner in;char* z;};
int main(){
 s1* points=new s1[5];points[0]={1,1,3,4,new char[7]};
 assert(points[0].x==1 && points[0].y==1 && points[0].in.f==3 && points[0].in.g==4);
 inner* p=&points[0].in;assert(p->f==3);
 delete[] points[0].z;delete[] points;
}
