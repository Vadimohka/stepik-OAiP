#include <stdio.h>
#include <stdlib.h>
#include <string.h>
 
#define YEAR_OFFSET 1890
 
typedef struct Model {
    int id;
    struct {
        int id;
        char *name;
    } make;
    char *name;
    unsigned char year; //year is an offset to 1890
} Model;
 
char* mallocByString(const char *str) { // функция, которая инициализирует поля типа char*
    char* p = (char*) malloc(strlen(str) + 1);
    strcpy(p, str);
    return p;
}
 
void freeModel(Model* model) { // очистка памяти
    free(model->make.name);
    free(model->name);
}
 
void xmlModel(Model *model) {
    printf("Some info");
}
 
int main() {
     
    Model cl;
    cl.id = 1;
    cl.make.id = 1;
    cl.make.name = mallocByString("Acura");
    cl.name = mallocByString("CL");
    cl.year = (2003 - YEAR_OFFSET);
 
    xmlModel(&cl);
    freeModel(&cl);

}
