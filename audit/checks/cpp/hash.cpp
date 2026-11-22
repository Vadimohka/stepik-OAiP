#include <memory>
#include <string>
#include <vector>
#include <iostream>
class Password { public: int id; std::string description,password; Password(int i,std::string d,std::string p):id(i),description(d),password(p){} void SetDescription(std::string s){description=s;} void SetPassword(std::string s){password=s;} };
class PasswordList { public: std::vector<std::shared_ptr<Password>> rows; std::shared_ptr<Password> SearchElementByID(int id){for(auto p:rows)if(p->id==id)return p;return{};} int GetCount(){return rows.size();} void AddElement(std::shared_ptr<Password> p){rows.push_back(p);} };
class HashTable { public: int tableSize,tableCount; PasswordList** items; HashTable(int); int CalculateHash(int); void InsertElement(int,std::string,std::string); ~HashTable(){for(int i=0;i<tableSize;++i)delete items[i];delete[] items;} };
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
    if (tableCount == tableSize) {
        return;
    }

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
int main(){HashTable h(1);h.InsertElement(1,"first","a");h.InsertElement(2,"second","b");h.InsertElement(1,"updated","a");std::cout<<h.items[0]->GetCount()<<":"<<h.items[0]->SearchElementByID(1)->description<<"\n";}
