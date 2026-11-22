#include <cstdio>
#include <limits>

// fd открыт в режиме "r+b"; по смещению pos ранее записан int
// той же реализацией программы. Например, pos = 0L — начало файла.
bool increment_counter(std::FILE* fd, long pos) {
    int counter{};
    if (fd == nullptr || std::fseek(fd, pos, SEEK_SET) != 0 ||
        std::fread(&counter, sizeof counter, 1, fd) != 1) {
        return false;
    }
    if (counter == std::numeric_limits<int>::max()) {
        return false; // увеличение не должно переполнить int
    }
    ++counter;
    if (std::fseek(fd, pos, SEEK_SET) != 0) {
        return false;
    }
    return std::fwrite(&counter, sizeof counter, 1, fd) == 1;
}
#include <cassert>
int main() {
    std::FILE* f=std::fopen("counter.bin","w+b"); assert(f);
    int value=5; assert(std::fwrite(&value,sizeof value,1,f)==1);
    assert(increment_counter(f,0));
    assert(std::fseek(f,0,SEEK_SET)==0); assert(std::fread(&value,sizeof value,1,f)==1); assert(value==6);
    value=std::numeric_limits<int>::max();
    assert(std::fseek(f,0,SEEK_SET)==0); assert(std::fwrite(&value,sizeof value,1,f)==1);
    assert(!increment_counter(f,0)); assert(!increment_counter(nullptr,0));
    std::fclose(f);
}
