# Исправления существующих шагов

Дата: 2026-11-23. Основа: `d936c0ee8d9f720ba26fec1b109a1153ae3b5930`.

**24 шагов в 16 уроках. Подготовлен; на Stepik этим пакетом не опубликован.**

P1 — неправильное поведение или оценивание; P2 — ошибка примера или объяснения. Приоритет описывает влияние на учебный материал, а не статус публикации.

| Шаг | ID | Приоритет | Подтверждённая ошибка | Изменяемые поля |
|---|---:|---|---|---|
| [1409621 / 1](https://stepik.org/lesson/1409621/step/1) | 5850209 | P2 | Проверка YAML → INI игнорировала значимые пробелы и начало ответа | `block.source.code`, `block.text` |
| [763639 / 3](https://stepik.org/lesson/763639/step/3) | 3177504 | P2 | Неразрывные пробелы делали копируемые примеры C++ некомпилируемыми | `block.text` |
| [763640 / 2](https://stepik.org/lesson/763640/step/2) | 3215105 | P2 | Неразрывные пробелы делали копируемые примеры C++ некомпилируемыми | `block.text` |
| [763719 / 2](https://stepik.org/lesson/763719/step/2) | 3177565 | P2 | Неразрывные пробелы делали копируемые примеры C++ некомпилируемыми | `block.text` |
| [763719 / 4](https://stepik.org/lesson/763719/step/4) | 3177651 | P2 | Неразрывные пробелы делали копируемые примеры C++ некомпилируемыми | `block.text` |
| [768143 / 7](https://stepik.org/lesson/768143/step/7) | 3267786 | P2 | Проверка точного вывода программы принимала неверный регистр | `block.source.case_sensitive` |
| [770586 / 6](https://stepik.org/lesson/770586/step/6) | 3438841 | P2 | Указатель вершины стека ошибочно объявлялся указателем на свободное место | `block.text` |
| [770586 / 12](https://stepik.org/lesson/770586/step/12) | 4700496 | P2 | В гарантии сравнения произведений использовались неопределённые x и y | `block.text` |
| [770587 / 4](https://stepik.org/lesson/770587/step/4) | 3213207 | P2 | Чтение слов дробило длинный ввод и могло принять его хвост за end | `block.text` |
| [770587 / 5](https://stepik.org/lesson/770587/step/5) | 3213210 | P2 | Чтение слов дробило длинный ввод и могло принять его хвост за end | `block.text` |
| [770589 / 15](https://stepik.org/lesson/770589/step/15) | 4949336 | P1 | Проверка теряла значимые крайние пробелы преобразуемого текста | `block.source.code`, `block.source.test_cases` |
| [770590 / 3](https://stepik.org/lesson/770590/step/3) | 3214910 | P2 | Возведение в степень вычисляло лишнее x*x при n=1 и срывало constexpr | `block.text` |
| [770596 / 3](https://stepik.org/lesson/770596/step/3) | 3215234 | P1 | Не проверяются ввод строк и выделение памяти для массива пользователей | `block.text` |
| [770596 / 6](https://stepik.org/lesson/770596/step/6) | 3215235 | P1 | mallocByString передаёт NULL в strcpy при отказе malloc | `block.text` |
| [770596 / 7](https://stepik.org/lesson/770596/step/7) | 3215236 | P1 | mallocByString передаёт NULL в strcpy при отказе malloc | `block.text` |
| [770597 / 1](https://stepik.org/lesson/770597/step/1) | 3212956 | P2 | Смена активного члена union ошибочно обещана для любой записи | `block.text` |
| [770597 / 3](https://stepik.org/lesson/770597/step/3) | 3215244 | P2 | Пример указателя использует ещё не объявленный Ints | `block.text` |
| [771130 / 3](https://stepik.org/lesson/771130/step/3) | 3215206 | P2 | Фрагмент дозаписи в файл не компилировался после копирования из-за U+00A0 | `block.text` |
| [853541 / 2](https://stepik.org/lesson/853541/step/2) | 3570303 | P1 | Неявное копирование RBT оставляет разные root у общего изменяемого дерева | `block.text` |
| [877083 / 3](https://stepik.org/lesson/877083/step/3) | 3669142 | P2 | В отрицательном friend-примере пропущены конец Storage и начало Display | `block.text` |
| [877083 / 6](https://stepik.org/lesson/877083/step/6) | 3669172 | P1 | Карточная игра читает неинициализированную chosen при неверном выборе | `block.text` |
| [877084 / 3](https://stepik.org/lesson/877084/step/3) | 3759850 | P1 | Неограниченный strcpy переполняет поля имён в примере виртуальной базы | `block.text` |
| [877084 / 5](https://stepik.org/lesson/877084/step/5) | 3759914 | P2 | Абстрактной базе ошибочно оставлено только наследование невиртуальных членов | `block.text` |
| [973831 / 2](https://stepik.org/lesson/973831/step/2) | 4035481 | P1 | Конструктор HashTable теряет выделения при неудачном создании списка; HashTable увеличивает tableCount до успешной вставки | `block.text` |

## 5850209: Проверка YAML → INI игнорировала значимые пробелы и начало ответа

[Текущий шаг](https://stepik.org/lesson/1409621/step/1) · [Исправленный файл](steps/1409621/01_5850209_code.step)

Проверка strip() принимала лишние пробелы в начале/конце ответа и пустую строку в начале при требовании точного формата INI. Условие также обещало обязательную последнюю пустую строку, которой нет в сохранённых эталонах.

Сравнение сохраняет все пробелы и внутренние переводы строк; нормализует CRLF и игнорирует только завершающие переводы строк. В условии явно описан этот допуск. Все 13 исходных наборов сохранены.

Для любого существующего clue исходный check(" " + clue, clue) возвращает True; новый — False. Независимый конвертер подтвердил 13 эталонов, включая глубину 499.

Проверка: [verify_yaml_ini.py](evidence/final_task/verify_yaml_ini.py), [results.json](evidence/final_task/results.json).


## 3177504: Неразрывные пробелы делали копируемые примеры C++ некомпилируемыми

[Текущий шаг](https://stepik.org/lesson/763639/step/3) · [Исправленный файл](steps/763639/03_3177504_text.step)

U+00A0 между токенами и перед инструкциями не является пробельным разделителем C++. GCC 14.2 в строгих режимах C++17 и C++20 отвергает исходные примеры. После замены на обычные пробелы проверенные фрагменты компилируются и дают заявленный результат. Это исправление исполняемости копируемого кода.

Проверка: [verify_fixes.py](evidence/foundations/verify_fixes.py), [fix_verification.json](evidence/foundations/fix_verification.json).


## 3215105: Неразрывные пробелы делали копируемые примеры C++ некомпилируемыми

[Текущий шаг](https://stepik.org/lesson/763640/step/2) · [Исправленный файл](steps/763640/02_3215105_text.step)

U+00A0 между токенами и перед инструкциями не является пробельным разделителем C++. GCC 14.2 в строгих режимах C++17 и C++20 отвергает исходные примеры. После замены на обычные пробелы проверенные фрагменты компилируются и дают заявленный результат. Это исправление исполняемости копируемого кода.

Проверка: [verify_fixes.py](evidence/foundations/verify_fixes.py), [fix_verification.json](evidence/foundations/fix_verification.json).


## 3177565: Неразрывные пробелы делали копируемые примеры C++ некомпилируемыми

[Текущий шаг](https://stepik.org/lesson/763719/step/2) · [Исправленный файл](steps/763719/02_3177565_text.step)

U+00A0 между токенами и перед инструкциями не является пробельным разделителем C++. GCC 14.2 в строгих режимах C++17 и C++20 отвергает исходные примеры. После замены на обычные пробелы проверенные фрагменты компилируются и дают заявленный результат. Это исправление исполняемости копируемого кода.

Проверка: [verify_fixes.py](evidence/foundations/verify_fixes.py), [fix_verification.json](evidence/foundations/fix_verification.json).


## 3177651: Неразрывные пробелы делали копируемые примеры C++ некомпилируемыми

[Текущий шаг](https://stepik.org/lesson/763719/step/4) · [Исправленный файл](steps/763719/04_3177651_text.step)

U+00A0 между токенами и перед инструкциями не является пробельным разделителем C++. GCC 14.2 в строгих режимах C++17 и C++20 отвергает исходные примеры. После замены на обычные пробелы проверенные фрагменты компилируются и дают заявленный результат. Это исправление исполняемости копируемого кода.

Проверка: [verify_fixes.py](evidence/foundations/verify_fixes.py), [fix_verification.json](evidence/foundations/fix_verification.json).


## 3267786: Проверка точного вывода программы принимала неверный регистр

[Текущий шаг](https://stepik.org/lesson/768143/step/7) · [Исправленный файл](steps/768143/07_3267786_string.step)

Вопрос просит вывод конкретной программы. На изображении литерал Hello, World!, а поток без uppercase печатает d и e в нижнем регистре. Изменён только флаг учёта регистра; шаблон, правила перевода строк, regex и пользовательский код не менялись. Вывод воспроизведён компиляцией программы с необходимыми заголовками в C++17 и C++20; проверка вариантов локальная, не отправка ответов на Stepik.

Проверка: [verify_fixes.py](evidence/foundations/verify_fixes.py), [fix_verification.json](evidence/foundations/fix_verification.json).


## 3438841: Указатель вершины стека ошибочно объявлялся указателем на свободное место

[Текущий шаг](https://stepik.org/lesson/770586/step/6) · [Исправленный файл](steps/770586/06_3438841_text.step)

**До исправления.** <p>В ячейках под соответствующими адресами лежат значения переменных <code>x</code>, <code>y</code> и <code>z</code>. Также стоит упомянуть, что в стеке всегда поддерживается указатель (<strong>SP - Stack Pointer</strong>), который указывает на вершину стека, то есть то место, в которое можно дальше записывать данные. Однако нам существование этого указателя погоды не делает, т.к. компилятор работает с ним самостоятельно.</p>

**После исправления.** <p>В ячейках под соответствующими адресами лежат значения переменных <code>x</code>, <code>y</code> и <code>z</code>. В типичной реализации процессор хранит указатель стека (<strong>SP — Stack Pointer</strong>; на x86-64 — <code>RSP</code>). Его точный смысл зависит от архитектуры. Например, на x86 инструкция <code>PUSH</code> сначала уменьшает указатель, а затем записывает значение по новому адресу. Поэтому текущую вершину нельзя считать свободной ячейкой для следующей записи. При выполнении обычного кода C++ необходимые операции со стеком формирует компилятор.</p>

На x86 PUSH сначала уменьшает SP/ESP/RSP и только затем записывает новый элемент. Текущая вершина может содержать уже размещённые данные, поэтому определение SP как места следующей свободной записи неверно даже для распространённой модели стека. Указана зависимость от архитектуры, без обещания устройства, обязательного для C++.

Проверка: [verify_fixes.py](evidence/foundations/verify_fixes.py), [fix_verification.json](evidence/foundations/fix_verification.json).


## 4700496: В гарантии сравнения произведений использовались неопределённые x и y

[Текущий шаг](https://stepik.org/lesson/770586/step/12) · [Исправленный файл](steps/770586/12_4700496_code.step)

**После исправления.** <p>Обозначим произведения <code>P = a<sub>1</sub> · ... · a<sub>n</sub></code> и <code>Q = b<sub>1</sub> · ... · b<sub>n</sub></code>. Гарантируется, что либо <code>P = Q</code>, либо <code>max(P, Q) / min(P, Q) &gt; 1 + 10<sup>−7</sup></code>. Эта гарантия относится к двум произведениям, а не к каждой паре входных элементов.</p>

Имена x и y в задаче не определены, а универсальная формула буквально неверна. Гарантия теперь явно относится к двум положительным произведениям и отдельно допускает равенство. Точная целочисленная проверка подтвердила эту гарантию и эталонные знаки для всех 31 подзадач в 12 сохранённых тестах. Проверяющий код и тесты не изменены.

Проверка: [verify_fixes.py](evidence/foundations/verify_fixes.py), [fix_verification.json](evidence/foundations/fix_verification.json), [check_task_references.py](evidence/foundations/check_task_references.py), [task_reference_results.json](evidence/foundations/task_reference_results.json).


## 3213207: Чтение слов дробило длинный ввод и могло принять его хвост за end

[Текущий шаг](https://stepik.org/lesson/770587/step/4) · [Исправленный файл](steps/770587/04_3213207_text.step)

Ширина %127s ограничивает только очередное чтение, а не длину слова во входе. Добавлена проверка границы слова до проверки команды end и сохранения строки. Слова до 127 байт, окончание ввода и расширение таблицы сохраняют прежнее поведение; слишком длинный ввод явно отвергается после освобождения ранее выделенных блоков.

Проверка: [verify_fixes.py](evidence/foundations/verify_fixes.py), [fix_verification.json](evidence/foundations/fix_verification.json), [word_reader_cases.json](evidence/foundations/word_reader_cases.json).


## 3213210: Чтение слов дробило длинный ввод и могло принять его хвост за end

[Текущий шаг](https://stepik.org/lesson/770587/step/5) · [Исправленный файл](steps/770587/05_3213210_text.step)

Ширина %127s ограничивает только очередное чтение, а не длину слова во входе. Добавлена проверка границы слова до проверки команды end и сохранения строки. Слова до 127 байт, окончание ввода и расширение таблицы сохраняют прежнее поведение; слишком длинный ввод явно отвергается после освобождения ранее выделенных блоков.

Проверка: [verify_fixes.py](evidence/foundations/verify_fixes.py), [fix_verification.json](evidence/foundations/fix_verification.json), [word_reader_cases.json](evidence/foundations/word_reader_cases.json).


## 4949336: Проверка теряла значимые крайние пробелы преобразуемого текста

[Текущий шаг](https://stepik.org/lesson/770589/step/15) · [Исправленный файл](steps/770589/15_4949336_code.step)

Условие требует сохранять пробелы. Для входа « x » точный ответ « ks », но strip() принимал неверный «ks». Для строки из трёх пробелов прежняя проверка принимала даже пустой ответ. Разрешены завершающие переводы строки, но пробелы остаются частью ответа.

Проверка: [fix_verification.json](evidence/core/fix_verification.json), [check_task_answers.py](evidence/core/check_task_answers.py), [task_answer_results.json](evidence/core/task_answer_results.json).


## 3214910: Возведение в степень вычисляло лишнее x*x при n=1 и срывало constexpr

[Текущий шаг](https://stepik.org/lesson/770590/step/3) · [Исправленный файл](steps/770590/03_3214910_text.step)

**До исправления.** После проверки n==0 функция сразу вычисляла exp(x*x, (n-1)/2)*x для нечётного n, включая n=1.

**После исправления.** Добавлен базовый случай n==1: return x; до умножения x*x.

exp(FLT_MAX,1) и exp(2.0f,127) имеют представимый результат, но прежняя функция вычисляет промежуточное переполняющееся x*x. GCC 14.2.0 в C++17 и C++20 отвергает такие константные выражения. Исправленный базовый случай убирает лишнюю операцию, сохраняя прежний алгоритм.

Проверка: [fix_verification.json](evidence/core/fix_verification.json), [constexpr_power_before.cpp](evidence/core/constexpr_power_before.cpp), [constexpr_power_after.cpp](evidence/core/constexpr_power_after.cpp), [constexpr_power_invalid_result.cpp](evidence/core/constexpr_power_invalid_result.cpp).


## 3215234: Не проверяются ввод строк и выделение памяти для массива пользователей

[Текущий шаг](https://stepik.org/lesson/770596/step/3) · [Исправленный файл](steps/770596/03_3215234_text.step)

**До исправления.** После EOF при чтении пароля программа использует старый buffer: ввод 1\nalice\n создаёт пароль alice. При отказе malloc используются нулевые указатели.

**После исправления.** Проверены все scanf и malloc, указатели всех строк заранее получают NULL, общий путь очистки освобождает частично заполненный массив. При ошибке программа возвращает 1.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3215234_stale_password_before.run.txt](evidence/advanced/logs/3215234_stale_password_before.run.txt), [3215234_allocation_failure_before.run.txt](evidence/advanced/logs/3215234_allocation_failure_before.run.txt), [validation_results.json](evidence/advanced/validation_results.json).


## 3215235: mallocByString передаёт NULL в strcpy при отказе malloc

[Текущий шаг](https://stepik.org/lesson/770596/step/6) · [Исправленный файл](steps/770596/06_3215235_text.step)

**До исправления.** mallocByString безусловно вызывает strcpy после malloc; код main не проверяет получение обеих строк.

**После исправления.** strcpy вызывается только после успешного выделения. main проверяет обе строки и вызывает существующую freeModel на пути ошибки, сохраняя нормальный пример.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3215235_allocation_failure_before.run.txt](evidence/advanced/logs/3215235_allocation_failure_before.run.txt), [validation_results.json](evidence/advanced/validation_results.json).


## 3215236: mallocByString передаёт NULL в strcpy при отказе malloc

[Текущий шаг](https://stepik.org/lesson/770596/step/7) · [Исправленный файл](steps/770596/07_3215236_text.step)

**До исправления.** mallocByString безусловно вызывает strcpy после malloc; код main не проверяет получение обеих строк.

**После исправления.** strcpy вызывается только после успешного выделения. main проверяет обе строки и вызывает существующую freeModel на пути ошибки, сохраняя нормальный пример.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3215236_allocation_failure_before.run.txt](evidence/advanced/logs/3215236_allocation_failure_before.run.txt), [validation_results.json](evidence/advanced/validation_results.json).


## 3212956: Смена активного члена union ошибочно обещана для любой записи

[Текущий шаг](https://stepik.org/lesson/770597/step/1) · [Исправленный файл](steps/770597/01_3212956_text.step)

**До исправления.** Фраза «запись в другой член меняет активный член» не ограничена типами/операциями. Присваивание неактивному std::string не начинает время жизни строки.

**После исправления.** Правило ограничено допустимыми встроенными/тривиальными операциями; пояснено, что нетривиальный член требует конструирования и уничтожения, прежний деструктор автоматически не вызывается.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3212956_explicit_lifetime.cpp](evidence/advanced/generated/3212956_explicit_lifetime.cpp), [3212956_explicit_lifetime.run.txt](evidence/advanced/logs/3212956_explicit_lifetime.run.txt).


## 3215244: Пример указателя использует ещё не объявленный Ints

[Текущий шаг](https://stepik.org/lesson/770597/step/3) · [Исправленный файл](steps/770597/03_3215244_text.step)

**До исправления.** В данном шаге и предыдущих шагах урока определён Floats, но Ints впервые определён только в следующем шаге. Показанный фрагмент не собирается в main: Ints was not declared.

**После исправления.** Перед использованием добавлено то же определение Ints с тремя целочисленными членами, которое используется далее в уроке.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3215244_before.compile.txt](evidence/advanced/logs/3215244_before.compile.txt), [3215244_after_c++20.compile.txt](evidence/advanced/logs/3215244_after_c++20.compile.txt).


## 3215206: Фрагмент дозаписи в файл не компилировался после копирования из-за U+00A0

[Текущий шаг](https://stepik.org/lesson/771130/step/3) · [Исправленный файл](steps/771130/03_3215206_text.step)

**До исправления.** Во втором <pre> 4 неразрывных пробела перед out << и 7 после out.close(); вне строк и комментариев.

**После исправления.** Ровно эти 11 U+00A0 заменены обычными пробелами в том же блоке кода.

Копирование отображаемого кода сохраняет U+00A0. GCC 14.2.0 сообщает extended character is not valid in an identifier в режимах C++17 и C++20. После замены фрагмент компилируется и дописывает Welcome to CPP, сохраняя ранее записанную строку.

Проверка: [fix_verification.json](evidence/core/fix_verification.json), [file_append_before.cpp](evidence/core/file_append_before.cpp), [file_append_after.cpp](evidence/core/file_append_after.cpp).


## 3570303: Неявное копирование RBT оставляет разные root у общего изменяемого дерева

[Текущий шаг](https://stepik.org/lesson/853541/step/2) · [Исправленный файл](steps/853541/02_3570303_text.step)

**До исправления.** После a.add(1), a.add(2), b=a, b.add(3) поворот изменяет общие узлы, но не a.root. В a исчезает ключ 2: contains(2) возвращает false. Неявное перемещение также отсутствует из-за объявленного деструктора и могло подменяться копированием.

**После исправления.** Конструктор копирования и копирующее присваивание явно удалены. Учебная реализация объявлена некопируемой и неперемещаемой; глубокое копирование не добавлялось. Основные операции дерева сохранены.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3570303_copy_before.run.txt](evidence/advanced/logs/3570303_copy_before.run.txt), [3570303_copy_after.compile.txt](evidence/advanced/logs/3570303_copy_after.compile.txt), [validate_invariants.py](evidence/advanced/validate_invariants.py), [invariant_results.json](evidence/advanced/invariant_results.json).


## 3669142: В отрицательном friend-примере пропущены конец Storage и начало Display

[Текущий шаг](https://stepik.org/lesson/877083/step/3) · [Исправленный файл](steps/877083/03_3669142_text.step)

**До исправления.** Намеренно неверное обращение к Display::displayItem дополнительно повреждено: конструктор Display и displayItem оказались внутри Storage, отсутствует m_displayIntFirst.

**После исправления.** Восстановлены границы двух классов и поле Display. Пример намеренно остаётся некомпилируемым из-за неполного Display в friend-объявлении и связанного отсутствия доступа к private; посторонние синтаксические ошибки устранены.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3669142_negative_before.compile.txt](evidence/advanced/logs/3669142_negative_before.compile.txt), [3669142_negative_after.compile.txt](evidence/advanced/logs/3669142_negative_after.compile.txt), [3669142_positive.run.txt](evidence/advanced/logs/3669142_positive.run.txt).


## 3669172: Карточная игра читает неинициализированную chosen при неверном выборе

[Текущий шаг](https://stepik.org/lesson/877083/step/6) · [Исправленный файл](steps/877083/06_3669172_text.step)

**До исправления.** card() оставляет number/suit без значений. При позиции 0, 4 или ошибке ввода switch не присваивает chosen, а isEqual затем читает эти поля.

**После исправления.** Конструктор по умолчанию создаёт двойку треф. main отклоняет нечисловой/отсутствующий ввод и позиции вне 1–3 до сравнения. Все три допустимых выбора сохраняют поведение игры.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3669172_before.compile.txt](evidence/advanced/logs/3669172_before.compile.txt), [validation_results.json](evidence/advanced/validation_results.json).


## 3759850: Неограниченный strcpy переполняет поля имён в примере виртуальной базы

[Текущий шаг](https://stepik.org/lesson/877084/step/3) · [Исправленный файл](steps/877084/03_3759850_text.step)

**До исправления.** unit/box принимают const char* без ограничения длины и копируют его в name[20], unit_box — в name[40]. Допустимая строка из 200 символов вызывает stack-buffer-overflow.

**После исправления.** Три поля имён хранят std::string; присваивание сохраняет строку целиком, для printf используется c_str(). Иерархия, виртуальная база и обычный вывод сохранены.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3759850_long_before.run.txt](evidence/advanced/logs/3759850_long_before.run.txt), [3759850_long_after.run.txt](evidence/advanced/logs/3759850_long_after.run.txt), [3759850_sample_c++20.run.txt](evidence/advanced/logs/3759850_sample_c++20.run.txt).


## 3759914: Абстрактной базе ошибочно оставлено только наследование невиртуальных членов

[Текущий шаг](https://stepik.org/lesson/877084/step/5) · [Исправленный файл](steps/877084/05_3759914_text.step)

**До исправления.** Текст говорит, что абстрактная база используется «для наследования невиртуальных элементов». Виртуальные функции также наследуются, включая конкретные реализации базы.

**После исправления.** Уточнено существование базового подобъекта и наследование обычных и виртуальных членов; для конкретного производного класса чистые виртуальные функции требуют конкретного окончательного переопределения.

Проверка: [validate_advanced.py](evidence/advanced/validate_advanced.py), [3759914_inherited_virtual.cpp](evidence/advanced/generated/3759914_inherited_virtual.cpp), [3759914_inherited_virtual.run.txt](evidence/advanced/logs/3759914_inherited_virtual.run.txt).


## 4035481: Конструктор HashTable теряет выделения при неудачном создании списка; HashTable увеличивает tableCount до успешной вставки

[Текущий шаг](https://stepik.org/lesson/973831/step/2) · [Исправленный файл](steps/973831/02_4035481_text.step)

**До исправления.** При отказе третьего new PasswordList остаются выделенными массив указателей и два списка. Деструктор HashTable не вызывается, потому что объект не достроен.

**После исправления.** Элементы массива указателей заранее равны nullptr; catch освобождает все уже созданные списки и сам массив и повторно выбрасывает исключение.

Проверка: [validate_hash.py](evidence/advanced/validate_hash.py), [4035481_ctor_before_c++20.run.txt](evidence/advanced/logs/4035481_ctor_before_c++20.run.txt), [4035481_ctor_after_c++20.run.txt](evidence/advanced/logs/4035481_ctor_after_c++20.run.txt), [hash_results.json](evidence/advanced/hash_results.json).

**До исправления.** При исключении из создания Password пустая цепочка остаётся пустой, но tableCount уже увеличен: воспроизведение даёт buckets=1 при entries=0.

**После исправления.** Признак пустой цепочки сохраняется заранее; tableCount увеличивается только после успешного AddElement. Отказ при создании Password оставляет оба счётчика равными нулю.

Проверка: [validate_hash.py](evidence/advanced/validate_hash.py), [4035481_insert_before.run.txt](evidence/advanced/logs/4035481_insert_before.run.txt), [4035481_insert_after.run.txt](evidence/advanced/logs/4035481_insert_after.run.txt), [hash_results.json](evidence/advanced/hash_results.json).
