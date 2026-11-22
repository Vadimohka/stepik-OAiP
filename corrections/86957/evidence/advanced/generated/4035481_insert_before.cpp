#include <memory>
#include <string>
#include <new>
class Password {
    int ID;
    std::string description;
    std::string password;

public:
    std::shared_ptr<Password> nextElement;

    Password(int IDInput, std::string descriptionInput,
             std::string passwordInput);

    int GetID();
    std::string GetDescription();
    std::string GetPassword();
    void SetDescription(std::string description);
    void SetPassword(std::string password);
};
class PasswordList {
protected:
    int count;
    std::shared_ptr<Password> head;
    std::shared_ptr<Password> tail;

public:
    PasswordList();
    std::shared_ptr<Password> GetHead();
    void AddElement(std::shared_ptr<Password> newElement);
    std::shared_ptr<Password> SearchElementByID(int IDToSearch);
    int GetCount();
};class HashTable {
    int tableSize;
    int tableCount;
    PasswordList** items;
    
public:
    HashTable(int tableSize);
    int BucketCount() const { return tableCount; } // test-only observation
    std::shared_ptr<Password> Lookup(int k) { return items[CalculateHash(k)]->SearchElementByID(k); }

    int CalculateHash(int ID);
    void InsertElement(int IDToAdd, std::string 
    descriptionToAdd, std::string passwordToAdd); 
    float CalculateNumberOfElements();
    float CalculateSumOfKeys();
    ~HashTable();
};
bool fail_password=false;
Password::Password(int id,std::string descriptionInput,std::string passwordInput)
    : ID(id),description(descriptionInput),password(passwordInput) {
    if(fail_password) throw std::bad_alloc{};
}
int Password::GetID(){return ID;}
std::string Password::GetDescription(){return description;}
std::string Password::GetPassword(){return password;}
void Password::SetDescription(std::string s){description=s;}
void Password::SetPassword(std::string s){password=s;}
PasswordList::PasswordList():count(0){}
std::shared_ptr<Password> PasswordList::GetHead(){return head;}
int PasswordList::GetCount(){return count;}
void PasswordList::AddElement(std::shared_ptr<Password> p){
    if(tail) tail->nextElement=p; else head=p;
    tail=p; ++count;
}
std::shared_ptr<Password> PasswordList::SearchElementByID(int id){
    auto p=head;
    while(p && p->GetID()!=id) p=p->nextElement;
    return p;
}
float HashTable::CalculateNumberOfElements(){
    int total=0;for(int i=0;i<tableSize;++i) total+=items[i]->GetCount();
    return static_cast<float>(total);
}
HashTable::HashTable(int tableSize) {
    this->tableSize = tableSize;
    this->tableCount = 0;

    items = new PasswordList*[tableSize];

    for (int i = 0; i < tableSize; i++) {
        items[i] = new PasswordList;
    }
}
int HashTable::CalculateHash(int ID) {
    return ID % tableSize;
}
void HashTable::InsertElement(int IDToAdd, std::string descriptionToAdd, std::string passwordToAdd) {
    int indexToInsert = CalculateHash(IDToAdd);

    PasswordList* passwordList = items[indexToInsert];
    
    std::shared_ptr<Password> existingPassword(passwordList->SearchElementByID(IDToAdd));
    if (existingPassword) {
        existingPassword->SetDescription(descriptionToAdd);
        existingPassword->SetPassword(passwordToAdd);
    } else {
        if (passwordList->GetCount() == 0) {
            this->tableCount++;
        }
        std::shared_ptr<Password> newPassword(new Password(IDToAdd, descriptionToAdd, passwordToAdd));
        passwordList->AddElement(newPassword);
    }
}
HashTable::~HashTable() {
    for(int i=0;i<tableSize;++i) delete items[i];
    delete[] items;
}

#include <cassert>
#include <iostream>
int main(){
    HashTable table(1);
    fail_password=true;
    try { table.InsertElement(1,"first","secret"); assert(false); }
    catch(const std::bad_alloc&) {}
    std::cout << "after failed insert: buckets=" << table.BucketCount()
              << ", entries=" << table.CalculateNumberOfElements() << '\n';
    if(table.BucketCount()!=0 || table.CalculateNumberOfElements()!=0) return 4;
    fail_password=false;
    table.InsertElement(1,"first","secret");
    table.InsertElement(2,"collision","other");
    table.InsertElement(1,"updated","new secret");
    assert(table.BucketCount()==1 && table.CalculateNumberOfElements()==2);
    assert(table.Lookup(1)->GetPassword()=="new secret");
    assert(table.Lookup(2)->GetPassword()=="other");
    std::cout << "successful inserts, collision and duplicate update passed\n";
}
