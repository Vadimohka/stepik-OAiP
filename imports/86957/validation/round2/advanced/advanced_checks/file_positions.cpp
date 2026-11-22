#include <cstdio>
#include <cassert>
#include <cstring>
int main() {
 const char* name="round2_file_test.bin";
 FILE* f=std::fopen(name,"w+b");assert(f);
 assert(std::fwrite("abc",1,3,f)==3);
 assert(std::fseek(f,-1,SEEK_END)==0);assert(std::ftell(f)==2);assert(std::fgetc(f)=='c');
 assert(std::fseek(f,0,SEEK_END)==0);assert(std::ftell(f)==3);assert(std::fclose(f)==0);
 f=std::fopen(name,"a+b");assert(f);assert(std::fseek(f,0,SEEK_SET)==0);assert(std::ftell(f)==0);
 assert(std::fputc('D',f)=='D');assert(std::fflush(f)==0);assert(std::fseek(f,0,SEEK_SET)==0);
 char data[5]{};assert(std::fread(data,1,4,f)==4);assert(std::strcmp(data,"abcD")==0);
 assert(std::fclose(f)==0);assert(std::remove(name)==0);
}
