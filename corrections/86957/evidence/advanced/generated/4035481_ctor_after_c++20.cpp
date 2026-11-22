
#include <cstdlib>
#include <cstdio>
#include <new>
#include <string>
int arrays=0, lists=0, attempt=0, fail_at=0;
void* operator new[](std::size_t n) {
    if(void* p=std::malloc(n)) { ++arrays; return p; }
    throw std::bad_alloc{};
}
void operator delete[](void* p) noexcept { if(p) --arrays; std::free(p); }
void operator delete[](void* p,std::size_t) noexcept { ::operator delete[](p); }
struct PasswordList {
    static void* operator new(std::size_t n) {
        if(++attempt==fail_at) throw std::bad_alloc{};
        if(void* p=std::malloc(n)) { ++lists; return p; }
        throw std::bad_alloc{};
    }
    static void operator delete(void* p) noexcept { if(p) --lists; std::free(p); }
};
class HashTable {
    int tableSize;
    int tableCount;
    PasswordList** items;
    
public:
    HashTable(int tableSize);
    int CalculateHash(int ID);
    void InsertElement(int IDToAdd, std::string 
    descriptionToAdd, std::string passwordToAdd); 
    float CalculateNumberOfElements();
    float CalculateSumOfKeys();
    ~HashTable();
};HashTable::HashTable(int tableSize) {
    this->tableSize = tableSize;
    this->tableCount = 0;

    items = new PasswordList*[tableSize]{};

    try {
        for (int i = 0; i < tableSize; i++) {
            items[i] = new PasswordList;
        }
    } catch (...) {
        for (int i = 0; i < tableSize; i++) {
            delete items[i]; // ещё не заполненные позиции равны nullptr
        }
        delete[] items;
        throw;
    }
}
HashTable::~HashTable() {
    for(int i=0;i<tableSize;++i) delete items[i];
    delete[] items;
}

int main(int argc,char** argv) {
    fail_at=argc>1 ? std::atoi(argv[1]) : 3;
    try { HashTable table(5); } catch(const std::bad_alloc&) {}
    std::printf("live arrays=%d, live lists=%d\n",arrays,lists);
    return arrays==0 && lists==0 ? 0 : 3;
}
