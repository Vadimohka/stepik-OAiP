
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
 
#define MAX_SIZE 20
 
typedef struct User {
    char *login;
    char *password;
    int id;
} User;
 
void jsonUser(User *user) {
    printf("{id: %d, login: \"%s\", password: \"%s\"}\n", 
            user->id, user->login, user->password);
}
 
void freeUsersArray(User** users, unsigned size) {
    unsigned i;
    for (i = 0; i < size; i++) {
        free((*users)[i].login);
        free((*users)[i].password);
    }
    free(*users);
}
 
int course_main() {
    User *users = NULL;
    unsigned size;
    char buffer[128];
    unsigned i;
 
    printf("Enter number of users: ");
    if (scanf("%u", &size) != 1) return 1;
 
    size = size <= MAX_SIZE? size: MAX_SIZE;
    users = (User*) malloc(size * sizeof(User));
    if (size != 0 && users == NULL) return 1;
    for (i = 0; i < size; i++) {
        users[i].login = NULL;
        users[i].password = NULL;
    }
 
    for (i = 0; i < size; i++) {
        printf("user #%u\nname: ", i);
        if (scanf("%127s", buffer) != 1) {
            freeUsersArray(&users, size);
            return 1;
        }
        users[i].id = i;
        users[i].login = (char*) malloc(strlen(buffer) + 1);
        if (users[i].login == NULL) {
            freeUsersArray(&users, size);
            return 1;
        }
        strcpy(users[i].login, buffer);
        printf("password: ");
        if (scanf("%127s", buffer) != 1) {
            freeUsersArray(&users, size);
            return 1;
        }
        users[i].password = (char*) malloc(strlen(buffer) + 1);
        if (users[i].password == NULL) {
            freeUsersArray(&users, size);
            return 1;
        }
        strcpy(users[i].password, buffer);
    }
 
    for (i = 0; i < size; i++) {
        jsonUser(&users[i]);
    }
 
    freeUsersArray(&users, size);

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
