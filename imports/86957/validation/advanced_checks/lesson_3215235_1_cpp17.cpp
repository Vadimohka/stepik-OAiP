#include <stdio.h>
 
typedef struct Model {
    int id;
    struct {
        int id;
        const char *name;
    } make;
    const char *name;
    unsigned char year; //year is an offset to 1890
} Model;
 
int main() {
    Model m = {10, {10, "Acura"}, "CL", 112};
    printf("Model name = %s\n", m.name);
    printf("Make name = %s\n", m.make.name);

}
