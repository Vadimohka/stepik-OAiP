#!/usr/bin/env python3
"""Reproduce three concrete corrections without changing the course snapshot."""
from copy import deepcopy
import html
import json
from pathlib import Path
import re
import subprocess
import tempfile

from check_task_answers import reform

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).parent
DEST = ROOT/'corrections/86957'


def original(sid):
    path = next((ROOT/'courses/86957/steps').rglob(f'*_{sid}_*.step'))
    return path, json.loads(path.read_text())


def save(path, document):
    destination = DEST/'steps'/path.parent.name/path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, ensure_ascii=False, indent=2)+'\n')
    return str(destination.relative_to(ROOT))


def code_block(document, index):
    text = re.findall(r'<pre[^>]*>(.*?)</pre>', document['block']['text'], re.S)[index]
    return html.unescape(re.sub('<[^>]+>', '', text))


def compile_case(name, source, standard, expect_success, run=False):
    source_path = OUT/(name+'.cpp')
    source_path.write_text(source)
    with tempfile.TemporaryDirectory(dir=OUT, prefix='compile_') as tmp:
        binary = Path(tmp)/'program'
        command = ['g++', '-std='+standard, '-Wall', '-Wextra', '-pedantic-errors', str(source_path), '-o', str(binary)]
        result = subprocess.run(command, capture_output=True, text=True)
        assert (result.returncode == 0) == expect_success, result.stderr
        report = {'name':name, 'standard':standard, 'expected_compile_success':expect_success,
                  'compile_returncode':result.returncode, 'diagnostics':result.stderr}
        if run:
            execution = subprocess.run([str(binary.resolve())], cwd=tmp, capture_output=True, text=True)
            assert execution.returncode == 0, execution.stderr
            report.update(run_returncode=execution.returncode, stdout=execution.stdout)
        return report


def main():
    findings=[]
    verification={'snapshot':'d936c0ee8d9f720ba26fec1b109a1153ae3b5930',
                  'compiler':subprocess.run(['g++','--version'],capture_output=True,text=True).stdout.splitlines()[0]}

    path, old = original(4949336)
    new = deepcopy(old)
    before = 'return reply.strip() == clue.strip()'
    after = 'return reply.rstrip("\\r\\n") == clue.rstrip("\\r\\n")'
    assert new['block']['source']['code'].count(before)==1
    new['block']['source']['code']=new['block']['source']['code'].replace(before,after)
    added=[[' x ', ' ks '], ['   ', '   '], [' QW ', '  ']]
    for dataset, clue in added:
        assert reform(dataset)==clue
    new['block']['source']['test_cases'].extend(added)
    oldns,newns={},{}
    exec(old['block']['source']['code'],oldns)
    exec(new['block']['source']['code'],newns)
    regressions=[]
    for dataset, clue in new['block']['source']['test_cases']:
        expected=reform(dataset.rstrip('\r\n'))
        assert expected==clue.rstrip('\r\n')
        for ending in ['', '\n', '\r\n']:
            assert newns['check'](expected+ending, clue) is True
    for dataset, clue in added:
        for wrong in sorted({clue.strip(), clue.lstrip(), clue.rstrip(), ' '+clue, clue+' '} - {clue}):
            assert newns['check'](wrong,clue) is False
            regressions.append({'input':dataset,'expected':clue,'reply':wrong,
                                'old_accepts':oldns['check'](wrong,clue),'fixed_accepts':newns['check'](wrong,clue)})
    assert newns['check']('ks ks', 'ksks') is False
    assert newns['check']('word ', 'word') is False
    assert newns['check']('', '') is True
    destination=save(path,new)
    verification['reform']={'stored_cases_independently_checked':25,'regression_cases_added':3,
                            'positive_checks_with_line_ending_variants':84,'negative_whitespace_checks':len(regressions)+2,
                            'counterexamples':regressions}
    findings.append({'step_id':4949336,'lesson_id':770589,'path':destination,'severity':'high',
                     'title':'Проверка теряла значимые крайние пробелы преобразуемого текста',
                     'before':{'block.source.code':before,'block.source.test_cases.count':25},
                     'after':{'block.source.code':after,'block.source.test_cases.count':28,'added_cases':added},
                     'rationale':'Условие требует сохранять пробелы. Для входа « x » точный ответ « ks », но strip() принимал неверный «ks». Для строки из трёх пробелов прежняя проверка принимала даже пустой ответ. Разрешены завершающие переводы строки, но пробелы остаются частью ответа.',
                     'changed_fields':['block.source.code','block.source.test_cases'],
                     'evidence':['corrections/86957/evidence/core/fix_verification.json','corrections/86957/evidence/core/check_task_answers.py','corrections/86957/evidence/core/task_answer_results.json'],
                     'source_urls':['https://stepik.org/lesson/770589/step/15']})

    path,old=original(3214910)
    new=deepcopy(old)
    before='if (n == 0)\n        return 1;\n    if (n % 2 == 0)'
    after='if (n == 0)\n        return 1;\n    if (n == 1)\n        return x;\n    if (n % 2 == 0)'
    assert new['block']['text'].count(before)==1
    new['block']['text']=new['block']['text'].replace(before,after)
    oldcode,newcode=code_block(old,0),code_block(new,0)
    suffix='\nconstexpr float maximum = std::numeric_limits<float>::max();\nstatic_assert(exp(maximum, 1) == maximum);\nint main() {}\n'
    full_tests='''
constexpr float maximum = std::numeric_limits<float>::max();
static_assert(exp(maximum, 0) == 1);
static_assert(exp(maximum, 1) == maximum);
static_assert(exp(-maximum, 1) == -maximum);
static_assert(exp(2.0f, 127) == 0x1p127f);
static_assert(exp(-2.0f, 127) == -0x1p127f);
static_assert(exp(0.0f, 0) == 1);
static_assert(exp(0.0f, 5) == 0);
static_assert(exp(2.0f, 10) == 1024);
static_assert(exp(-2.0f, 9) == -512);
static_assert(exp(0.5f, 3) == 0.125f);
int main() {
    for (float base : {-2.0f, -1.0f, 0.0f, 0.5f, 1.0f, 2.0f}) {
        float expected = 1.0f;
        for (int n=0; n<=20; ++n) {
            if (exp(base,n) != expected) return 1;
            expected *= base;
        }
    }
}
'''
    compilation=[]
    for standard in ['c++17','c++20']:
        compilation.append(compile_case('constexpr_power_before','#include <limits>\n'+oldcode+suffix,standard,False))
        compilation.append(compile_case('constexpr_power_after','#include <limits>\n#include <initializer_list>\n'+newcode+full_tests,standard,True,True))
        compilation.append(compile_case('constexpr_power_invalid_result','#include <limits>\n'+newcode+'\nconstexpr float overflow = exp(std::numeric_limits<float>::max(), 2);\nint main() {}\n',standard,False))
    verification['constexpr_power']=compilation
    destination=save(path,new)
    findings.append({'step_id':3214910,'lesson_id':770590,'path':destination,'severity':'medium',
                     'title':'Возведение в степень вычисляло лишнее x*x при n=1 и срывало constexpr',
                     'before':'После проверки n==0 функция сразу вычисляла exp(x*x, (n-1)/2)*x для нечётного n, включая n=1.',
                     'after':'Добавлен базовый случай n==1: return x; до умножения x*x.',
                     'rationale':'exp(FLT_MAX,1) и exp(2.0f,127) имеют представимый результат, но прежняя функция вычисляет промежуточное переполняющееся x*x. GCC 14.2.0 в C++17 и C++20 отвергает такие константные выражения. Исправленный базовый случай убирает лишнюю операцию, сохраняя прежний алгоритм.',
                     'changed_fields':['block.text'],
                     'evidence':['corrections/86957/evidence/core/fix_verification.json','corrections/86957/evidence/core/constexpr_power_before.cpp','corrections/86957/evidence/core/constexpr_power_after.cpp','corrections/86957/evidence/core/constexpr_power_invalid_result.cpp'],
                     'source_urls':['https://stepik.org/lesson/770590/step/3']})

    path,old=original(3215206)
    new=deepcopy(old)
    pre_blocks=list(re.finditer(r'<pre[^>]*>(.*?)</pre>',new['block']['text'],re.S))
    target=pre_blocks[1]
    original_html=target.group(0)
    assert code_block(old,1).count('\xa0')==11
    corrected_html=original_html.replace('&nbsp;',' ').replace('\xa0',' ')
    new['block']['text']=new['block']['text'][:target.start()]+corrected_html+new['block']['text'][target.end():]
    header='#include <fstream>\n#include <iostream>\n#include <iterator>\n#include <string>\nint main() {\n'
    seed='    { std::ofstream seed("D:\\\\hello.txt"); seed << "Hello\\n"; }\n'
    tail='''
    std::ifstream check("D:\\\\hello.txt");
    const std::string actual((std::istreambuf_iterator<char>(check)), {});
    return actual == "Hello\\nWelcome to CPP\\n" ? 0 : 1;
}
'''
    # The fragment is pasted unchanged; only surrounding headers/main/test fixture are added.
    compilation=[]
    for standard in ['c++17','c++20']:
        compilation.append(compile_case('file_append_before',header+seed+code_block(old,1)+'\n'+tail,standard,False))
        compilation.append(compile_case('file_append_after',header+seed+code_block(new,1)+'\n'+tail,standard,True,True))
    verification['file_append']=compilation
    destination=save(path,new)
    findings.append({'step_id':3215206,'lesson_id':771130,'path':destination,'severity':'medium',
                     'title':'Фрагмент дозаписи в файл не компилировался после копирования из-за U+00A0',
                     'before':'Во втором <pre> 4 неразрывных пробела перед out << и 7 после out.close(); вне строк и комментариев.',
                     'after':'Ровно эти 11 U+00A0 заменены обычными пробелами в том же блоке кода.',
                     'rationale':'Копирование отображаемого кода сохраняет U+00A0. GCC 14.2.0 сообщает extended character is not valid in an identifier в режимах C++17 и C++20. После замены фрагмент компилируется и дописывает Welcome to CPP, сохраняя ранее записанную строку.',
                     'changed_fields':['block.text'],
                     'evidence':['corrections/86957/evidence/core/fix_verification.json','corrections/86957/evidence/core/file_append_before.cpp','corrections/86957/evidence/core/file_append_after.cpp'],
                     'source_urls':['https://stepik.org/lesson/771130/step/3']})

    (OUT/'fix_verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
    (DEST/'core_findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'fixed_steps':[f['step_id'] for f in findings], 'reform':verification['reform'], 'compilation_checks':sum(len(verification[k]) for k in ['constexpr_power','file_append'])},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
