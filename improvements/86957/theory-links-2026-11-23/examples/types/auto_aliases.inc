const int original{7};
auto copy = original;            // int: отдельная изменяемая копия
auto& same = original;           // const int&: ссылка на original
const auto& read_only = copy;    // const int&: чтение copy без копии
copy = 9;
// original == 7, same == 7, read_only == 9
