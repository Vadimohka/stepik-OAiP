"""Produce the human-readable evidence index and precise per-step coverage."""
from pathlib import Path
from collections import Counter
import json
import re
import html
from course_blocks import ROOT, LESSONS, source_path, step, blocks

BASE='d936c0ee8d9f720ba26fec1b109a1153ae3b5930'
PREFIX='corrections/86957/evidence/advanced/'
SOURCES={
    'malloc': {'title':'WG14 N1570, 7.22.3.3–4: free and malloc','url':'https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf','ref':'turn739526059view2'},
    'scanf': {'title':'WG14 N1570, 7.21.6.2/4: scanf returns assignments or EOF','url':'https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf','ref':'turn132443602view1'},
    'strcpy': {'title':'WG14 N1570, 7.24.2.3: strcpy copies through the terminating zero','url':'https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf','ref':'turn132443602view2'},
    'lookup': {'title':'C++ draft [basic.lookup]: a declaration is required','url':'https://eel.is/c++draft/basic.lookup','ref':'turn201531919view2'},
    'union': {'title':'C++20 draft N4861 [class.union]: active member and lifetime-start rules','url':'https://timsong-cpp.github.io/cppwp/n4861/class.union','ref':'turn739526059view1'},
    'friend': {'title':'C++ draft [class.friend]: friendship to a member function','url':'https://eel.is/c++draft/class.friend','ref':'turn928146024view2'},
    'indet': {'title':'C++20 draft N4861 [basic.indet]: use of indeterminate int/enum values','url':'https://timsong-cpp.github.io/cppwp/n4861/basic.indet','ref':'turn201531919view0'},
    'abstract': {'title':'C++ draft [class.abstract]: abstract bases and inherited virtual functions','url':'https://eel.is/c++draft/class.abstract','ref':'turn928146024view3'},
    'copy': {'title':'C++ draft [class.copy.ctor]: implicit public copy and suppression of move','url':'https://eel.is/c++draft/class.copy.ctor','ref':'turn928146024view0'},
    'except': {'title':'C++ draft [except.ctor]: unwinding a failed constructor','url':'https://eel.is/c++draft/except.ctor','ref':'turn402292240view0'},
}

findings=[]
def add(sid,severity,title,before,after,evidence,sources,locations):
    p=source_path(sid)
    findings.append({'finding_id':f'advanced-{len(findings)+1:03}',
        'step_id':str(sid),'lesson_id':p.parent.name,'severity':severity,'title':title,
        'before':before,'after':after,'changed_fields':['block.text'],
        'changed_locations':locations,'evidence':[PREFIX+x for x in evidence],
        'sources':[SOURCES[x] for x in sources],
        'source_file':str(p.relative_to(ROOT)),
        'corrected_file':f'corrections/86957/steps/{p.parent.name}/{p.name}',
        'base_commit':BASE})

add(3215234,'high','Не проверяются ввод строк и выделение памяти для массива пользователей',
    'После EOF при чтении пароля программа использует старый buffer: ввод 1\\nalice\\n создаёт пароль alice. При отказе malloc используются нулевые указатели.',
    'Проверены все scanf и malloc, указатели всех строк заранее получают NULL, общий путь очистки освобождает частично заполненный массив. При ошибке программа возвращает 1.',
    ['validate_advanced.py','logs/3215234_stale_password_before.run.txt','logs/3215234_allocation_failure_before.run.txt','validation_results.json'],
    ['scanf','malloc'],['Первый и единственный кодовый блок: инициализация указателей, проверки ввода/выделения, ранняя очистка; пояснение после кода.'])
for sid in (3215235,3215236):
    add(sid,'high','mallocByString передаёт NULL в strcpy при отказе malloc',
        'mallocByString безусловно вызывает strcpy после malloc; код main не проверяет получение обеих строк.',
        'strcpy вызывается только после успешного выделения. main проверяет обе строки и вызывает существующую freeModel на пути ошибки, сохраняя нормальный пример.',
        ['validate_advanced.py',f'logs/{sid}_allocation_failure_before.run.txt','validation_results.json'],
        ['malloc','strcpy'],['Кодовый блок 0: mallocByString и проверка двух строк в main; пояснение пути отказа.'])
add(3215244,'medium','Пример указателя использует ещё не объявленный Ints',
    'В данном шаге и предыдущих шагах урока определён Floats, но Ints впервые определён только в следующем шаге. Показанный фрагмент не собирается в main: Ints was not declared.',
    'Перед использованием добавлено то же определение Ints с тремя целочисленными членами, которое используется далее в уроке.',
    ['validate_advanced.py','logs/3215244_before.compile.txt','logs/3215244_after_c++20.compile.txt'],
    ['lookup'],['В начало кодового блока добавлено определение используемого union.'])
add(3212956,'medium','Смена активного члена union ошибочно обещана для любой записи',
    'Фраза «запись в другой член меняет активный член» не ограничена типами/операциями. Присваивание неактивному std::string не начинает время жизни строки.',
    'Правило ограничено допустимыми встроенными/тривиальными операциями; пояснено, что нетривиальный член требует конструирования и уничтожения, прежний деструктор автоматически не вызывается.',
    ['validate_advanced.py','generated/3212956_explicit_lifetime.cpp','logs/3212956_explicit_lifetime.run.txt'],
    ['union'],['Последний абзац о размере и активном члене.'])
add(3669142,'medium','В отрицательном friend-примере пропущены конец Storage и начало Display',
    'Намеренно неверное обращение к Display::displayItem дополнительно повреждено: конструктор Display и displayItem оказались внутри Storage, отсутствует m_displayIntFirst.',
    'Восстановлены границы двух классов и поле Display. Пример намеренно остаётся некомпилируемым из-за неполного Display в friend-объявлении и связанного отсутствия доступа к private; посторонние синтаксические ошибки устранены.',
    ['validate_advanced.py','logs/3669142_negative_before.compile.txt','logs/3669142_negative_after.compile.txt','logs/3669142_positive.run.txt'],
    ['friend','lookup'],['Кодовый блок 1 — только восстановление структуры намеренно ошибочного примера.'])
add(3669172,'high','Карточная игра читает неинициализированную chosen при неверном выборе',
    'card() оставляет number/suit без значений. При позиции 0, 4 или ошибке ввода switch не присваивает chosen, а isEqual затем читает эти поля.',
    'Конструктор по умолчанию создаёт двойку треф. main отклоняет нечисловой/отсутствующий ввод и позиции вне 1–3 до сравнения. Все три допустимых выбора сохраняют поведение игры.',
    ['validate_advanced.py','logs/3669172_before.compile.txt','validation_results.json'],
    ['indet'],['Кодовый блок 0: <clocale>, конструктор card и проверка позиции; соответствующее пояснение; return логического выражения больше не называется условной операцией.'])
add(3759850,'high','Неограниченный strcpy переполняет поля имён в примере виртуальной базы',
    'unit/box принимают const char* без ограничения длины и копируют его в name[20], unit_box — в name[40]. Допустимая строка из 200 символов вызывает stack-buffer-overflow.',
    'Три поля имён хранят std::string; присваивание сохраняет строку целиком, для printf используется c_str(). Иерархия, виртуальная база и обычный вывод сохранены.',
    ['validate_advanced.py','logs/3759850_long_before.run.txt','logs/3759850_long_after.run.txt','logs/3759850_sample_c++20.run.txt'],
    ['strcpy'],['Кодовый блок 4: только хранение/копирование/вывод имён и нужный заголовок; пояснение об аргументах-строках.'])
add(3759914,'medium','Абстрактной базе ошибочно оставлено только наследование невиртуальных членов',
    'Текст говорит, что абстрактная база используется «для наследования невиртуальных элементов». Виртуальные функции также наследуются, включая конкретные реализации базы.',
    'Уточнено существование базового подобъекта и наследование обычных и виртуальных членов; для конкретного производного класса чистые виртуальные функции требуют конкретного окончательного переопределения.',
    ['validate_advanced.py','generated/3759914_inherited_virtual.cpp','logs/3759914_inherited_virtual.run.txt'],
    ['abstract'],['Одно предложение в объяснении абстрактных классов заменено точным описанием.'])
add(3570303,'high','Неявное копирование RBT оставляет разные root у общего изменяемого дерева',
    'После a.add(1), a.add(2), b=a, b.add(3) поворот изменяет общие узлы, но не a.root. В a исчезает ключ 2: contains(2) возвращает false. Неявное перемещение также отсутствует из-за объявленного деструктора и могло подменяться копированием.',
    'Конструктор копирования и копирующее присваивание явно удалены. Учебная реализация объявлена некопируемой и неперемещаемой; глубокое копирование не добавлялось. Основные операции дерева сохранены.',
    ['validate_advanced.py','logs/3570303_copy_before.run.txt','logs/3570303_copy_after.compile.txt','validate_invariants.py','invariant_results.json'],
    ['copy'],['Полный каркас RBT: две декларации = delete; пояснение владения после каркаса.'])
add(4035481,'high','Конструктор HashTable теряет выделения при неудачном создании списка',
    'При отказе третьего new PasswordList остаются выделенными массив указателей и два списка. Деструктор HashTable не вызывается, потому что объект не достроен.',
    'Элементы массива указателей заранее равны nullptr; catch освобождает все уже созданные списки и сам массив и повторно выбрасывает исключение.',
    ['validate_hash.py','logs/4035481_ctor_before_c++20.run.txt','logs/4035481_ctor_after_c++20.run.txt','hash_results.json'],
    ['except'],['Кодовый блок 0: нулевая инициализация массива указателей и очистка в обработчике.'])
add(4035481,'medium','HashTable увеличивает tableCount до успешной вставки',
    'При исключении из создания Password пустая цепочка остаётся пустой, но tableCount уже увеличен: воспроизведение даёт buckets=1 при entries=0.',
    'Признак пустой цепочки сохраняется заранее; tableCount увеличивается только после успешного AddElement. Отказ при создании Password оставляет оба счётчика равными нулю.',
    ['validate_hash.py','logs/4035481_insert_before.run.txt','logs/4035481_insert_after.run.txt','hash_results.json'],
    ['except'],['Кодовый блок 2: перенос инкремента после добавления; пояснение пути исключения.'])

selection={3215234:[0],3215235:[0],3215236:[0],3215244:[0],3669142:[1,3],
           3669172:[0],3759850:[4],3570303:[1],3570281:[0],3570213:[0],3570166:[0],4035481:[0,1,2]}
for sid in (3570304,3570333):selection[sid]=list(range(len(blocks(sid))))
changed_ids={int(f['step_id']) for f in findings}
covered=[]
counts=Counter()
for lesson in LESSONS:
    for p in sorted((ROOT/'courses/86957/steps'/str(lesson)).glob('*.step')):
        d=json.loads(p.read_text());sid=int(d['id']);kind=d['block']['name'];counts[kind]+=1
        bs=blocks(sid)
        covered.append({'step_id':str(sid),'lesson_id':str(lesson),'file':str(p.relative_to(ROOT)),
            'block_type':kind,'html_text_read':True,'source_and_options_read':kind!='text',
            'assessment_key_reviewed':kind in ('choice','fill-blanks','code'),
            'assessment_key_modified':False,'all_code_blocks_executed':False,
            'compiled_code_block_indexes':selection.get(sid,[]),
            'selected_examples_or_counterexamples_executed':sid in selection or sid in (3212956,3759914),
            'code_block_count':len(bs),'nbsp_in_code':any('\u00a0' in b for b in bs),
            'media_or_linked_content_viewed':False,
            'status':'corrected_confirmed_defect' if sid in changed_ids else 'read_review_no_change',
            'limitation':'Просмотр текста/ключей не доказывает отсутствие других ошибок. Рисунки и внешние материалы отдельно не проверялись.'})
        if kind=='code':
            covered[-1]['independent_reference_solution_executed']=False
            covered[-1]['grader_source_executed']=False
            covered[-1]['stored_test_count']=len(d['block'].get('source',{}).get('test_cases',[]))
            if sid==5070446:
                covered[-1]['limitation']=('Прочитаны условие, check и 34 сохранённых набора; проверены число наборов и баланс скобок. '
                    'Независимый интерпретатор не написан, правильность всех 34 эталонов не подтверждена. '
                    'Условие не определяет полностью связь ссылки-результата функции с объектом; дополнительные предположения не внесены.')
                covered[-1]['source_context']={'url':'https://codeforces.com/gym/104255/problems?locale=ru',
                    'title':'Codeforces Gym 104255, задача G: Borrow checker',
                    'verified_by':'root',
                    'note':'Первоисточник повторяет нынешнюю семантику. Общего правила привязки возвращаемой ссылки к существующему объекту при проверке не найдено.'}
            else:
                covered[-1]['limitation']='Намеренно ошибочный исходник и эталон прочитаны; независимое исправленное решение не запускалось. Формат эталона не изменялся.'

coverage={'base_commit':BASE,'modules':list(range(12,20)),'lessons':LESSONS,
          'step_count':len(covered),'types':dict(counts),'corrected_step_count':len(changed_ids),
          'finding_count':len(findings),'coverage':covered,
          'verification':{'compiler':'g++ 14.2.0','standards':'C++17 and C++20 for selected corrected examples; C++20 for invariant harnesses',
             'commands':['python3 corrections/86957/evidence/advanced/validate_advanced.py',
                         'python3 corrections/86957/evidence/advanced/validate_invariants.py',
                         'python3 corrections/86957/evidence/advanced/validate_hash.py'],
             'sanitizers':'AddressSanitizer and UBSan on selected cases. LeakSanitizer disabled because this environment reports ptrace incompatibility; allocation/free counters cover the selected failure paths.',
             'tree_coverage':'20000 deterministic mixed operations each for AVL and RBT, seed 86957; every state compared with std::map and checked for structural invariants.',
             'grading_changes':'None. Existing choice keys, fill-blank keys and code graders were read, not replaced.',
             'limitations':['Не компилировались все фрагменты каждого шага; намеренно ошибочные примеры не объявлены исправными.',
                            'Хеш-таблица показана частично: тесты дополняют пропущенные методы простым совместимым списком; проверяется именно показанный код конструктора/вставки.',
                            'Расширение RBT итератором в3570332 — незавершённые фрагменты, не проверялось как готовая библиотека.',
                            'Рисунки/внешние ссылки/видео не просматривались; проверены HTML и доступные поля оценивания.']},
          'excluded_candidates':[
              {'step_id':'4047616','reason':'Отсутствие delete в коротком фрагменте преобразования не доказывает утечку полной программы: p остаётся доступен. Cleanup-правка исключена.'},
              {'step_id':'3759927','reason':'После минимального исправления компиляции printf с шириной даёт иные внутренние пробелы, но условие явно требует подогнать вывод под sample. Изменение эталона сочтено неоднозначным и исключено.'}],
          'already_correct_on_current_snapshot':[
              {'step_id':'3570166','note':'Nested-owner LearningOwner уже исправлен в current; повторный ASan/UBSan запуск даёт42/0/2/0. Не зарегистрирован как новый дефект.'},
              {'step_id':'3570281','note':'Удаление в AVL копирует и ключ, и значение; проверки не воспроизвели прежнюю ошибку.'}]}

if __name__=='__main__':
    assert len(covered)==115 and not any(s['nbsp_in_code'] for s in covered)
    out=ROOT/'corrections/86957'
    (out/'advanced_findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2)+'\n')
    (out/'advanced_coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
    # Only block.text is edited; ID, time, keys, templates and structure remain intact.
    for sid in changed_ids:
        old,new=step(sid),step(sid,True)
        old['block']['text']=new['block']['text']
        assert old==new,sid
    print(f'Wrote {len(findings)} findings for {len(changed_ids)} corrected steps; read coverage {len(covered)} steps.')
