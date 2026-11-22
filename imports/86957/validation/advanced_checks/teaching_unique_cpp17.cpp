// Учебный вариант для одиночного объекта T (не для массива).
template<class T>
class unique_ptr {
private:
    T* m_ptr;

public:
    explicit operator bool() const {
        return m_ptr != nullptr;
    }

    explicit unique_ptr(T* ptr = nullptr) {
        m_ptr = ptr;
    }

    // Деструктор позаботится об удалении указателя
    ~unique_ptr() {
         delete m_ptr;
    }

    // Конструктор перемещения, который передает право собственности на x.m_ptr в m_ptr
    unique_ptr(unique_ptr&& x) {
        m_ptr = x.m_ptr;
        x.m_ptr = nullptr;
    }

    unique_ptr(const unique_ptr& x) = delete;

    unique_ptr& operator=(const unique_ptr& a) = delete;

    // Оператор присваивания перемещением, который передает право собственности на x.m_ptr в m_ptr
    unique_ptr& operator=(unique_ptr&& x) {
        // Проверка на самоприсваивание
        if (&x == this)
            return *this;

        // Удаляем всё, что к этому моменту может хранить указатель 
        delete m_ptr;

        // Передаем право собственности на x.m_ptr в m_ptr
        m_ptr = x.m_ptr;
        x.m_ptr = nullptr; // мы поговорим об этом чуть позже

        return *this;
    }

    T& operator*() const {
        return *m_ptr;
    }

    T* operator->() const {
        return m_ptr;
    }

    bool isNull() const { 
        return m_ptr == nullptr;
    }
};

#include <cassert>
#include <type_traits>
#include <utility>
int main() {
    static_assert(!std::is_convertible_v<unique_ptr<int>,bool>);
    unique_ptr<int> a(new int(7)); assert(a && *a==7);
    unique_ptr<int> b(std::move(a)); assert(a.isNull() && *b==7);
    b=std::move(b); assert(*b==7);
    unique_ptr<int> c; c=std::move(b); assert(b.isNull() && *c==7);
}
