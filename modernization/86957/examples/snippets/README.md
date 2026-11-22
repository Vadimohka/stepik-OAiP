# GoogleTest: проверенный дополнительный практикум

Фрагмент `gtest_assertions.cpp` соответствует шагу 3253553. Теперь он проверен
с настоящим GoogleTest **v1.17.0**, commit
`52eb8108c5bdec04579160ae17225d66034bd723` из официального репозитория
<https://github.com/google/googletest.git>. Зависимость закреплена по commit. Её исходники загружаются отдельно.

## Отдельный учебный проект

Положите в одну папку четыре файла:

- `CMakeLists.txt` и `gtest_assertions.cpp` из этого каталога;
- `interesting.cpp` и `interesting.hpp` из соседнего `../tooling/interesting`.

В этой папке выполните:

```text
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --config Debug
ctest --test-dir build -C Debug --output-on-failure --no-tests=error
```

Первая настройка загружает закреплённый официальный commit, поэтому нужны Git
и доступ к GitHub. `CMAKE_BUILD_TYPE` используется одноконфигурационными
генераторами; `--config`/`-C` выбирают конфигурацию у Visual Studio и других
многоконфигурационных генераторов.

В проект входят только тестовый фрагмент, одна реализация `interesting.cpp`
и GoogleTest. `GTest::gtest_main` предоставляет `main`. Прежние `main.cpp`
приложения и `tests.cpp` из самостоятельного CTest-практикума в новую цель
не включаются. CTest должен обнаружить и успешно выполнить два теста:

- `InterestingNumbers.HandlesCarryBoundary`;
- `StringComparisons.ComparesContents`.

Для проверки C++17 добавьте к настройке `-DCMAKE_CXX_STANDARD=17`.
По умолчанию выбирается C++20.

## Проверка непосредственно из репозитория

Копировать исходники необязательно: `INTERESTING_SOURCE_DIR` позволяет указать
каталог существующей общей реализации. Из корня репозитория задайте этот
параметр абсолютным путём к `modernization/86957/examples/tooling/interesting`.
Например, заменив `ABSOLUTE_PATH_TO_INTERESTING` действительным путём:

```text
cmake -S modernization/86957/examples/snippets -B build-googletest -DCMAKE_BUILD_TYPE=Debug -DINTERESTING_SOURCE_DIR=ABSOLUTE_PATH_TO_INTERESTING
cmake --build build-googletest --config Debug
ctest --test-dir build-googletest -C Debug --output-on-failure --no-tests=error
```

Если официальный source уже скачан и проверен, можно дополнительно передать
`-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=ABSOLUTE_PATH_TO_GOOGLETEST`. Такой override
доверяет содержимому указанного каталога: предварительно проверьте его commit
и отсутствие локальных изменений. При выполненной проверке использовался
именно чистый checkout закреплённого SHA вне репозитория курса.

## Результат реальной проверки

Linux, GCC 14.2.0, CMake 4.4.5; C++17 и C++20; Debug с `-Werror`.
Оба именованных теста прошли через CTest в обоих режимах. Исполняемый файл
GoogleTest дополнительно запущен напрямую и выдал JSON-отчёт без отказов.
Windows/MSVC и Stepik не запускались.

`verification.json` хранит версии, commit зависимости, команды и SHA-256 всех
четырёх входных файлов. `manifest.json` сохраняет `kind: "fragment"`, потому что
файл зависит от GoogleTest и общей библиотеки, но его статус проверки теперь
`passed_with_real_dependency`. Общий валидатор курса может проверять HTML
отдельно от этого запуска с внешней зависимостью.
