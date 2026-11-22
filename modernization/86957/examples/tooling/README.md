# Практикумы по CMake и модульному тестированию

Код совпадает с примерами в обновлённых шагах 3231317, 3253429 и 3253503.
Файлы не требуют загрузки внешних библиотек. Для сборки нужны CMake 3.22+
и компилятор с поддержкой выбранного C++20.

## Первая программа

Из каталога `hello` при использовании Make или Ninja:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
./build/hello
```

Ожидается `Hello C++` и перевод строки.

## Общая реализация и тесты

Из каталога `interesting` при использовании Make или Ninja:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON
cmake --build build
ctest --test-dir build --output-on-failure --no-tests=error
```

Приложение `interesting_app` и тестовая программа `interesting_tests`
связаны с одной библиотекой `interesting`. Тестовая программа выполняет
13 явных проверок и при успехе печатает `13 checks passed`.
CTest регистрирует её как один тест. Для просмотра вывода успешного теста
добавьте параметр `-V`.

Для генератора Visual Studio конфигурацию задают при сборке и тестировании:

```text
cmake -S . -B build -DBUILD_TESTING=ON
cmake --build build --config Debug
ctest --test-dir build -C Debug --output-on-failure --no-tests=error
```

## Проверка материалов

Из корня репозитория:

```bash
python3 modernization/86957/examples/tooling/verify.py
```

Если CMake не находится в `PATH`, укажите `--cmake /путь/к/cmake`.
Скрипт использует GCC и генератор Unix Makefiles; `--compiler` позволяет
указать другой доступный GCC-совместимый компилятор. Все сборки и намеренные
изменения выполняются во временном каталоге.

Проверяются:

- сохранность всех полей шагов, кроме текста;
- совпадение семи файлов с кодом в HTML;
- реальные CMake-сборки Debug и Release;
- точный вывод приложения для 13 входов, включая ошибочный ввод;
- строгая компиляция C++17/C++20 с `-Werror` и `NDEBUG`;
- отказ CTest при намеренно неверном ожидании;
- обнаружение ошибки в рабочей реализации формулы;
- сравнение с независимым подсчётом суммы цифр для 10 001 значения.

`examples.json` описывает файлы и ожидаемые результаты.
`validation.json` содержит результат последнего успешного запуска.
Windows/MSVC и подключение GoogleTest в этом окружении не запускались.
