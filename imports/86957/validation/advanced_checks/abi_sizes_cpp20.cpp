typedef struct inner {
    bool x;
    char z;
    int y;
} inner;
#pragma pack(push, 2)
struct T {
    int i;
    short j;
    double k;
    inner in;
};
#pragma pack(pop)
struct inner_reordered { int y; bool x; char z; };
#pragma pack(push,2)
struct T_reordered { double k; int i; inner_reordered in; short j; };
#pragma pack(pop)
struct alignas(16) ArrayOfChars { char A[10]; char B[8]; };
static_assert(sizeof(bool)==1 && sizeof(char)==1 && sizeof(int)==4 && alignof(int)==4);
static_assert(sizeof(short)==2 && sizeof(double)==8 && alignof(double)==8);
static_assert(sizeof(inner)==8 && sizeof(inner_reordered)==8);
static_assert(sizeof(T)==22 && sizeof(T_reordered)==22);
static_assert(sizeof(ArrayOfChars)==32);
union Padded { int x; char bytes[5]; };
static_assert(sizeof(Padded)>5);
int main() {}
