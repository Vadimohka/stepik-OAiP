#include <memory>
#include <string>
#include <cassert>
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
};
class HashTable {
    friend struct HashProbe;
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
};
Password::Password(int i,std::string d,std::string p):ID(i),description(d),password(p){}
int Password::GetID(){return ID;}
std::string Password::GetDescription(){return description;}
std::string Password::GetPassword(){return password;}
void Password::SetDescription(std::string v){description=v;}
void Password::SetPassword(std::string v){password=v;}
PasswordList::PasswordList():count(0){}
std::shared_ptr<Password> PasswordList::GetHead(){return head;}
int PasswordList::GetCount(){return count;}
void PasswordList::AddElement(std::shared_ptr<Password> p) {
    if(tail)tail->nextElement=p;else head=p;tail=p;++count;
}
std::shared_ptr<Password> PasswordList::SearchElementByID(int id) {
    for(auto p=head;p;p=p->nextElement)if(p->GetID()==id)return p;return {};
}
HashTable::~HashTable(){for(int i=0;i<tableSize;++i)delete items[i];delete[] items;}
struct HashProbe {
    static int used(const HashTable& t){return t.tableCount;}
    static int count(const HashTable& t){int n=0;for(int i=0;i<t.tableSize;++i)n+=t.items[i]->GetCount();return n;}
    static auto get(const HashTable& t,int id){return t.items[id%t.tableSize]->SearchElementByID(id);}
};
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
int main(){
    HashTable t(1);t.InsertElement(1,"first","a");t.InsertElement(2,"second","b");t.InsertElement(1,"updated","c");
    assert(HashProbe::used(t)==1 && HashProbe::count(t)==2);
    assert(HashProbe::get(t,1)->GetDescription()=="updated" && HashProbe::get(t,1)->GetPassword()=="c");
    assert(HashProbe::get(t,2)->GetDescription()=="second");
    HashTable u(3);for(int i=0;i<20;++i)u.InsertElement(i,"v","p");
    for(int i=0;i<20;++i)u.InsertElement(i,"new","newp");
    assert(HashProbe::used(u)==3 && HashProbe::count(u)==20);
    for(int i=0;i<20;++i)assert(HashProbe::get(u,i)->GetPassword()=="newp");
}
