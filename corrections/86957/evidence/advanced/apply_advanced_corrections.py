"""Reproduce the narrowly scoped corrections from the untouched course snapshot."""
from pathlib import Path
import copy
import html
import json
import re
from course_blocks import ROOT, source_path, step, blocks

changed = {}


def get(step_id):
    if step_id not in changed:
        changed[step_id] = copy.deepcopy(step(step_id))
    return changed[step_id]


def replace(step_id, old, new):
    d = get(step_id)
    assert old in d['block']['text'], (step_id, old)
    d['block']['text'] = d['block']['text'].replace(old, new)


def code(step_id, index, replacement):
    d = get(step_id)
    matches = list(re.finditer(r'<pre[^>]*>(.*?)</pre>', d['block']['text'], re.S))
    m = matches[index]
    inner = m.group(1)
    c = re.search(r'(<code\b[^>]*>).*?(</code>)', inner, re.S)
    if c:
        inner = inner[:c.start()] + c.group(1) + html.escape(replacement, quote=False) + c.group(2) + inner[c.end():]
    else:
        inner = html.escape(replacement, quote=False)
    t = d['block']['text']
    d['block']['text'] = t[:m.start(1)] + inner + t[m.end(1):]


# The C allocation example already frees all members on normal completion.
# Initialize every pointer first, then use the same cleanup on early failure.
s = blocks(3215234)[0]
s = s.replace('    users = (User*) malloc(size * sizeof(User));', '''    users = (User*) malloc(size * sizeof(User));
    if (size != 0 && users == NULL) return 1;
    for (i = 0; i < size; i++) {
        users[i].login = NULL;
        users[i].password = NULL;
    }''')
s = s.replace('        scanf("%127s", buffer);', '''        if (scanf("%127s", buffer) != 1) {
            freeUsersArray(&users, size);
            return 1;
        }''')
for field in ('login', 'password'):
    needle = f'        users[i].{field} = (char*) malloc(strlen(buffer) + 1);'
    s = s.replace(needle, needle + f'''
        if (users[i].{field} == NULL) {{
            freeUsersArray(&users, size);
            return 1;
        }}''')
code(3215234, 0, s)
replace(3215234, 'Поэтому в этом примере сначала освобождаем строки каждого пользователя, затем сам массив.',
        'Поэтому в этом примере сначала освобождаем строки каждого пользователя, затем сам массив. '
        'Перед вводом все указатели на строки получают NULL: так общая функция очистки безопасна и при частично заполненном массиве. '
        'Результаты scanf и malloc проверяются; при конце ввода или отказе выделения памяти программа освобождает уже полученную память и завершается с кодом 1.')

for sid in (3215235, 3215236):
    s = blocks(sid)[0]
    s = s.replace('    strcpy(p, str);', '    if (p != NULL) strcpy(p, str);')
    needle = '    cl.name = mallocByString("CL");'
    s = s.replace(needle, needle + '''
    if (cl.make.name == NULL || cl.name == NULL) {
        freeModel(&cl);
        return 1;
    }''')
    code(sid, 0, s)
    get(sid)['block']['text'] += ('\n<p>mallocByString возвращает NULL при отказе выделения памяти и не вызывает strcpy с нулевым указателем. '
                                 'После получения обеих строк main проверяет результат. При ошибке freeModel освобождает успешно выделенные строки; free(NULL) допустим.</p>')

# This example precedes the first definition of Ints in the next step.
s = blocks(3215244)[0]
code(3215244, 0, '''union Ints {
    unsigned short int a;
    unsigned int b;
    unsigned long int c;
};

''' + s)

# Assignment does not universally start the lifetime of a class member in a union.
replace(3212956, 'В каждый момент обычно активен только один член union; запись в другой член меняет активный член.',
        'В каждый момент активен не более чем один член union. Для простых членов, как int или double в следующих примерах, '
        'встроенное присваивание может начать время жизни нового члена и закончить время жизни прежнего. '
        'Это не общее правило для любого класса: например, присваивание неактивному полю std::string не создаёт строку. '
        'Для нетривиальных членов нужно отдельно управлять конструированием и уничтожением; union не вызывает деструктор прежнего члена автоматически.')

# Preserve the intentional incomplete-class error, remove unrelated malformed class syntax.
s = blocks(3669142)[1]
needle = '    // Ошибка: Storage не увидел полное определение класса Display\n \npublic:'
assert needle in s
s = s.replace(needle, '''    // Ошибка: Storage не увидел полное определение класса Display
};

class Display {
private:
    bool m_displayIntFirst;

public:''')
code(3669142, 1, s)

# An invalid choice used to leave chosen.number and chosen.suit indeterminate.
s = blocks(3669172)[0]
s = s.replace('#include <iostream>', '#include <iostream>\n#include <clocale>', 1)
s = s.replace('    card() {}', '    card() : number(2), suit(clubs) {}')
s = s.replace('    std::cin >> position; // ввод позиции игроком', '''    if (!(std::cin >> position) || position < 1 || position > 3) {
        std::cout << "Ошибка: введите номер позиции от 1 до 3.\\n";
        return 1;
    }''')
code(3669172, 0, s)
replace(3669172, 'которые не инициализируются при создании.',
        'которые при создании получают значение «двойка треф». До сравнения выбранной карты main проверяет успешность ввода и диапазон позиции 1–3; неверный ввод завершает программу до сравнения.')
replace(3669172, 'Для сравнения используется условная операция.', 'Для сравнения используется логическое выражение с операциями == и &amp;&amp;.')
replace(3669172, 'однако условная операция обеспечивает более краткую форму записи.', 'однако прямой возврат логического выражения обеспечивает более краткую форму записи.')

# Keep the inheritance example and its output, remove the unchecked fixed capacity.
s = blocks(3759850)[4]
assert 'struct unit : virtual public price' in s
s = s.replace('#include <cstring>', '#include <string>')
s = s.replace('char name[20];', 'std::string name;').replace('char name[40];', 'std::string name;')
s = s.replace('strcpy(name, x);', 'name = x;').replace('strcpy(name, z);', 'name = z;')
s = s.replace('name, val, type);', 'name.c_str(), val, type);')
s = s.replace('printf("\\nUNIT_BOX %s,", name);', 'printf("\\nUNIT_BOX %s,", name.c_str());')
s = s.replace('box::name, unit::name);', 'box::name.c_str(), unit::name.c_str());')
code(3759850, 4, s)
get(3759850)['block']['text'] += ('\n<p>Имена хранятся в std::string, поэтому более длинное название не переполняет фиксированный массив символов. '
                                'При выводе через printf("%s", ...) используется c_str(); аргументы конструкторов должны указывать на существующие нуль-терминированные строки.</p>')

replace(3759914, 'Абстрактный класс можно использовать только в качестве базового для наследования невиртуальных элементов в производных классах.',
        'Объект абстрактного класса может существовать как базовый подобъект производного класса. '
        'Производный класс наследует как обычные члены, так и виртуальные функции; конкретные виртуальные функции могут сохранять реализацию базы, '
        'а для создания объекта все чисто виртуальные функции должны получить конкретное окончательное переопределение.')

s = blocks(3570303)[1]
s = s.replace('    ~RBT() = default;', '''    ~RBT() = default;
    RBT(const RBT&) = delete;
    RBT& operator=(const RBT&) = delete;''')
code(3570303, 1, s)
get(3570303)['block']['text'] += ('\n<p>В этом учебном варианте дерево нельзя копировать или перемещать. '
                                'Неявная копия shared_ptr-корня дала бы двум объектам общее изменяемое дерево, но отдельные указатели root: '
                                'поворот при вставке в одну копию мог бы оставить другой объект с прежним корнем и потерянной частью ключей. '
                                'Для поддержки копирования потребовалась бы отдельная реализация независимой копии всех узлов. '
                                'После явного запрета копирования и пользовательского объявления деструктора неявные операции перемещения также не создаются.</p>')

# The destructor of a HashTable whose construction throws is not invoked.
# Initialize all slots, clean up constructed lists, and rethrow the failure.
s = blocks(4035481)[0]
s = s.replace('    items = new PasswordList*[tableSize];', '    items = new PasswordList*[tableSize]{};')
s = s.replace('''    for (int i = 0; i < tableSize; i++) {
        items[i] = new PasswordList;
    }''', '''    try {
        for (int i = 0; i < tableSize; i++) {
            items[i] = new PasswordList;
        }
    } catch (...) {
        for (int i = 0; i < tableSize; i++) {
            delete items[i]; // ещё не заполненные позиции равны nullptr
        }
        delete[] items;
        throw;
    }''')
code(4035481, 0, s)
s = blocks(4035481)[2]
s = s.replace('''        if (passwordList->GetCount() == 0) {
            this->tableCount++;
        }''', '        const bool wasEmpty = passwordList->GetCount() == 0;')
s = s.replace('        passwordList->AddElement(newPassword);', '''        passwordList->AddElement(newPassword);
        if (wasEmpty) {
            this->tableCount++;
        }''')
code(4035481, 2, s)
get(4035481)['block']['text'] += ('\n<p>Если создание одного из списков выбросит исключение, конструктор освобождает уже созданные списки и массив указателей, затем передаёт исключение дальше. '
                                'Деструктор самого HashTable при неудачном конструировании не вызывается. '
                                'В InsertElement счётчик непустых списков меняется после успешного добавления: отказ при создании нового Password не должен увеличивать tableCount.</p>')

if __name__ == '__main__':
    for sid, d in changed.items():
        src = source_path(sid)
        dst = ROOT / 'corrections/86957/steps' / src.parent.name / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    print('Corrected steps:', ', '.join(map(str, changed)))
