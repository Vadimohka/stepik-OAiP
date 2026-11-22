#include <cassert>
int initialized = 0;
__attribute__((constructor)) void prepare() { initialized=42; }
int main() { assert(initialized==42); }
