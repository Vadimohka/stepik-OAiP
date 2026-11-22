
#include <stdio.h>
#include <stdlib.h>
static int calls = 0;
static int live = 0;
static void* injected_malloc(size_t size) {
    const char* setting = getenv("FAIL_AT");
    if (++calls == (setting ? atoi(setting) : 0)) return NULL;
    void* p = malloc(size);
    if (p) ++live;
    return p;
}
static void injected_free(void* p) {
    if (p) --live;
    free(p);
}
#define malloc injected_malloc
#define free injected_free
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
 
#define YEAR_OFFSET 1890
 
//Отдельно выделили структуру "Марка"
typedef struct Make {
    int id;
    char *name;
} Make;
 
//Теперь полем структуры "Модель" является структура "Марка"
typedef struct Model {
    int id;
    Make make;
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
 
int course_main() {
    Make *make = NULL;
    Model cl;
    int *id;
 
    cl.id = 2;
    cl.make.id = 1;
    cl.make.name = mallocByString("Acura");
    cl.name = mallocByString("CL");
    cl.year = (2003 - YEAR_OFFSET);
 
    //Получаем указатель на вложенную структуру
    make = &cl.make;
    //Получаем указатель на поле структуры
    id = &cl.id;
    printf("make.name = %s\n", make->name);
    printf("make.id = %d\n", make->id);
    printf("model.id = %d\n", *id);
 
    freeModel(&cl);
    return 0;
}
#undef malloc
#undef free
int main() {
    int rc = course_main();
    if (live != 0) {
        fprintf(stderr, "unreleased allocations: %d\n", live);
        return 97;
    }
    return rc;
}
