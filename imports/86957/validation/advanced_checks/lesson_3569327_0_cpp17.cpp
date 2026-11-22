#include <iostream>
#include <memory>

struct X {};

int main() {
    auto ptr = std::make_shared<X>();
    {
        auto ptr2 = ptr;
        std::cout << ptr.use_count() << '\n'; // 2
    }
    std::cout << ptr.use_count() << '\n'; // 1
} // последний shared_ptr уничтожается, затем уничтожается X
