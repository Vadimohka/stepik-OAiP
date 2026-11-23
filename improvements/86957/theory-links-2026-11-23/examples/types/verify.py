#!/usr/bin/env python3
"""Current author checks for the targeted LINKS corrections; no learner tasks."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
ROOT = HERE.parents[4]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def code_blocks(text):
    return [html.unescape(re.sub('<[^>]+>', '', s)) for s in re.findall(r'<pre\b[^>]*><code\b[^>]*>(.*?)</code></pre>', text, re.S)]


def main():
    changes = json.loads((PKG/'changes_types.json').read_text())
    checks = []
    snapshots = []
    documents = {}
    unchanged = 0
    for row in changes:
        sid = row['step_id']
        source = ROOT/'courses/86957'/row['path']
        target = PKG/row['path']
        before = json.loads(source.read_text())
        after = json.loads(target.read_text())
        control = deepcopy(after)
        control['block']['text'] = before['block']['text']
        assert control == before, f'Non-text mutation: {sid}'
        old = code_blocks(before['block']['text'])
        new = code_blocks(after['block']['text'])
        if sid == 3212920:
            assert old[0].replace('        return 0;\n','        return 1;\n') == new[0]
            assert old[1:] == new[1:]
        elif sid == 3214974:
            assert old == new[:-1]
            assert len(new) == len(old) + 1
        elif sid == 3213209:
            assert old[:2] == new[:2] and old[3:] == new[3:]
            erase_comments = lambda code: re.sub(r'//[^\n]*','',code)
            assert erase_comments(old[2]) == erase_comments(new[2])
        else:
            assert old == new, f'Unexpected code change: {sid}'
            unchanged += 1
        snapshots.append({'step_id':sid,'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target.read_bytes()),'text_sha256':sha(after['block']['text'].encode()),'code_blocks':len(new),'code_change': 'return_code' if sid == 3212920 else 'added_fragment' if sid == 3214974 else 'comments_only' if sid == 3213209 else 'none'})
        documents[sid] = after
    bounds = code_blocks(documents[3212920]['block']['text'])[0]
    fragment = code_blocks(documents[3214974]['block']['text'])[-1]
    (HERE/'bounds.cpp').write_text(bounds)
    (HERE/'auto_aliases.inc').write_text(fragment)

    harness = '''#include <cstddef>
#include <iostream>
#include <type_traits>
#include <vector>

int main() {
'''+fragment+'''
    static_assert(std::is_same_v<decltype(copy), int>);
    static_assert(std::is_same_v<decltype(same), const int&>);
    static_assert(std::is_same_v<decltype(read_only), const int&>);
    static_assert(std::is_same_v<decltype(nullptr), std::nullptr_t>);
    int* empty = nullptr;
    static_assert(std::is_same_v<decltype(empty), int*>);
    const std::vector<int> count_value(3, 0);
    const std::vector<int> elements{3, 0};
    if (empty != nullptr || count_value != std::vector<int>{0, 0, 0}
                         || elements != std::vector<int>({3, 0})) {
        return 1;
    }
    static_assert((2 << 2) == 8 && (16 >> 3) == 2);
    static_assert((5 | 2) == 7 && (6 & 2) == 2 && (5 ^ 2) == 7);
#if __cplusplus >= 202002L
    static_assert((~9) == -10);
    static_assert((-9 >> 1) == -5);
#endif
    std::cout << original << ' ' << same << ' ' << read_only << '\\n';
}
'''
    (HERE/'semantic_checks.cpp').write_text(harness)
    compiler = os.environ.get('CXX','g++')
    assert shutil.which(compiler), 'G++ is required'
    compiler_version = subprocess.run([compiler,'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
    cases = [
        ('0\n','10\n',0), ('1\n','20\n',0), ('2\n','30\n',0), ('3\n','40\n',0),
        ('-1\n','INVALID\n',1), ('4\n','INVALID\n',1),
        ('2147483647\n','INVALID\n',1), ('-2147483648\n','INVALID\n',1),
        ('','INVALID\n',1), ('abc\n','INVALID\n',1),
        ('999999999999999999999999999999999999\n','INVALID\n',1),
        ('2 trailing text\n','30\n',0),
        ('1x\n','20\n',0), ('1 2\n','20\n',0),
    ]
    compiles = 0
    expected_failures = 0
    executions = 0
    with tempfile.TemporaryDirectory(prefix='stepik-links-types-') as temporary:
        temporary = Path(temporary)
        for standard in ('c++17','c++20'):
            for name in ('bounds','semantic_checks'):
                executable = temporary/(name+'-'+standard)
                command = [compiler,'-std='+standard,'-Wall','-Wextra','-Wpedantic','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',str(HERE/(name+'.cpp')),'-o',str(executable)]
                result = subprocess.run(command,capture_output=True,text=True,timeout=60)
                compiles += 1
                assert result.returncode == 0, result.stderr
                checks.append({'kind':'compile','standard':standard,'source':name+'.cpp','flags':command[1:-3],'result':'passed'})
                program_cases = cases if name == 'bounds' else [('', '7 7 9\n', 0)]
                for input_text, output, status in program_cases:
                    result = subprocess.run([str(executable)],input=input_text,capture_output=True,text=True,timeout=10)
                    executions += 1
                    assert (result.returncode,result.stdout,result.stderr) == (status,output,''), (name,input_text,result)
                    checks.append({'kind':'run','standard':standard,'program':name,'input':input_text,'expected_stdout':output,'expected_exit_code':status,'observed_stdout':result.stdout,'observed_stderr':result.stderr,'observed_exit_code':result.returncode,'result':'passed'})
            for alias in ('same','read_only'):
                invalid = temporary/('invalid-'+alias+'.cpp')
                invalid.write_text(harness.replace('copy = 9;',alias+' = 9;'))
                result = subprocess.run([compiler,'-std='+standard,'-Wall','-Wextra','-Wpedantic','-c',str(invalid),'-o',str(temporary/'invalid.o')],capture_output=True,text=True,timeout=60)
                expected_failures += 1
                assert result.returncode != 0 and ('read-only' in result.stderr or 'const' in result.stderr), result.stderr
                checks.append({'kind':'expected_compile_rejection','standard':standard,'operation':alias+' = 9;','source_sha256':sha(invalid.read_bytes()),'observed_exit_code':result.returncode,'result':'passed'})
    report = {
        'schema_version':1,'status':'passed','checked_at':datetime.now(timezone.utc).isoformat(),
        'base_commit':'352c2796717a55f4f0db8395b7d6093d8d67c35e',
        'command':'python3 improvements/86957/theory-links-2026-11-23/examples/types/verify.py',
        'environment':{'system':platform.system(),'machine':platform.machine(),'python':platform.python_version(),'compiler':compiler_version},
        'counts':{'changed_steps':len(changes),'steps_with_code_blocks_preserved':unchanged,'successful_compilations':compiles,'expected_compile_rejections':expected_failures,'executions':executions,'standards':['C++17','C++20']},
        'step_inputs':snapshots,
        'sources':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())} for p in (HERE/'bounds.cpp',HERE/'auto_aliases.inc',HERE/'semantic_checks.cpp',HERE/'verify.py')],
        'checks':checks,
        'limits':[
            'Это новый запуск проверки адресных изменений LINKS, не перезапись исторических validation.json.',
            'Полная программа с индексом компилируется из точного кода обновлённого .step. Новый фрагмент auto включён в авторский harness без изменения.',
            'Дополнительные проверки различия скобок vector, типа nullptr и допустимых сдвигов проверяют сформулированные в текстах частные случаи; они не доказывают все положения стандарта.',
            'В 25 изменённых шагах все pre/code-блоки сохранены побайтно после HTML-декодирования. В 3213209 меняется только комментарий фрагмента; исходная полная программа сохранена. Полная программа T3 в 3214974 сохранена.',
            'Остальные старые полные программы не пересобираются в этом запуске. Windows/MSVC и macOS не проверялись. Stepik не читается и не изменяется.'
        ]
    }
    (HERE/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'counts':report['counts']},ensure_ascii=False))


if __name__ == '__main__':
    main()
