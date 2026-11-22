"""Compile and execute focused regressions for modules 12–19.

Generated translations retain the course code verbatim except for explicitly
documented harness adaptations (main renaming and allocation-failure injection).
Deliberate failures are expected only for the original defect reproductions.
"""
from pathlib import Path
import json
import os
import subprocess
from course_blocks import ROOT, blocks, rbt

HERE = Path(__file__).resolve().parent
BUILD = ROOT.parent / '_work/advanced_build'
BUILD.mkdir(parents=True, exist_ok=True)
(HERE / 'generated').mkdir(exist_ok=True)
(HERE / 'logs').mkdir(exist_ok=True)
results = []


def run(command, *, data='', env=None):
    return subprocess.run(command, input=data, text=True, capture_output=True,
                          timeout=30, env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0', **(env or {})})


def compile_case(name, source, std='c++20', sanitize=False, should_compile=True):
    path = HERE / 'generated' / (name + '.cpp')
    path.write_text(source)
    executable = BUILD / name
    command = ['g++', '-std=' + std, '-Wall', '-Wextra', '-pedantic-errors',
               '-g', '-O1', str(path), '-o', str(executable)]
    if sanitize:
        command += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    '-fno-pie', '-no-pie']
    r = run(command)
    (HERE / 'logs' / (name + '.compile.txt')).write_text(r.stdout + r.stderr)
    results.append({'case': name, 'phase': 'compile', 'standard': std,
                    'sanitizers': sanitize, 'returncode': r.returncode,
                    'expected_success': should_compile})
    assert (r.returncode == 0) == should_compile, (name, r.stderr)
    return executable, r


def execute(name, executable, *, data='', env=None, expected=0, contains=None, excludes=None):
    r = run([str(executable)], data=data, env=env)
    (HERE / 'logs' / (name + '.run.txt')).write_text(r.stdout + r.stderr)
    results.append({'case': name, 'phase': 'run', 'returncode': r.returncode,
                    'expected': expected, 'input': data,
                    'stdout': r.stdout, 'stderr_log': 'logs/' + name + '.run.txt'})
    assert (r.returncode == expected if isinstance(expected, int) else r.returncode != 0), (name, r.stdout, r.stderr)
    if contains is not None:
        assert contains in r.stdout + r.stderr, (name, contains, r.stdout, r.stderr)
    if excludes is not None:
        assert excludes not in r.stdout + r.stderr, (name, excludes, r.stdout, r.stderr)
    return r


def allocation_harness(s):
    s = s.replace('int main()', 'int course_main()')
    # main's implicit return 0 does not apply after renaming to course_main.
    last = s.rfind('}')
    s = s[:last] + '    return 0;\n' + s[last:]
    return r'''
#include <stdio.h>
#include <stdlib.h>
static int calls = 0;
static int live = 0;
static void* injected_malloc(size_t size) {
    const char* setting = getenv("FAIL_AT");
    if (++calls == (setting ? atoi(setting) : 0)) return NULL;
    void* p = malloc(size);
    if (p) ++live;
    return p;
}
static void injected_free(void* p) {
    if (p) --live;
    free(p);
}
#define malloc injected_malloc
#define free injected_free
''' + s + r'''
#undef malloc
#undef free
int main() {
    int rc = course_main();
    if (live != 0) {
        fprintf(stderr, "unreleased allocations: %d\n", live);
        return 97;
    }
    return rc;
}
'''


def main():
    # C examples: complete normal inputs, EOF, and every allocation failure site.
    for sid in (3215234, 3215235, 3215236):
        before, _ = compile_case(f'{sid}_before', allocation_harness(blocks(sid)[0]), sanitize=True)
        execute(f'{sid}_allocation_failure_before', before, env={'FAIL_AT': '1'},
                data='1\nalice\nsecret\n' if sid == 3215234 else '', expected='failure',
                contains='runtime error')
        for std in ('c++17', 'c++20'):
            name = f'{sid}_after_{std}'
            after, _ = compile_case(name, allocation_harness(blocks(sid, True)[0]), std, sanitize=True)
            data = '1\nalice\nsecret\n' if sid == 3215234 else ''
            execute(name + '_normal', after, data=data, excludes='runtime error')
            for failure in range(1, 4 if sid == 3215234 else 3):
                execute(name + f'_fail_{failure}', after, data=data,
                        env={'FAIL_AT': str(failure)}, expected=1, excludes='runtime error')
            if sid == 3215234:
                for index, malformed in enumerate(('', '1\n', '1\nalice\n')):
                    execute(name + f'_eof_{index}', after, data=malformed, expected=1, excludes='runtime error')
                execute(name + '_empty_array', after, data='0\n', excludes='runtime error')
        if sid == 3215234:
            execute('3215234_stale_password_before', before, data='1\nalice\n',
                    contains='password: "alice"')

    # The pointer-to-union example used an as-yet undefined type.
    compile_case('3215244_before', 'int main(){\n' + blocks(3215244)[0] + '\n}', should_compile=False)
    for std in ('c++17', 'c++20'):
        exe, _ = compile_case('3215244_after_' + std, 'int main(){\n' + blocks(3215244, True)[0] + '\n}', std, True)
        execute('3215244_after_' + std, exe)

    # Intentionally failing friend example remains negative, but no malformed Display constructor.
    prefix = '#include <iostream>\n'
    _, original = compile_case('3669142_negative_before', prefix + blocks(3669142)[1], should_compile=False)
    _, fixed = compile_case('3669142_negative_after', prefix + blocks(3669142, True)[1], should_compile=False)
    assert 'expected unqualified-id' in original.stderr
    assert 'expected unqualified-id' not in fixed.stderr
    assert 'incomplete type' in fixed.stderr
    exe, _ = compile_case('3669142_positive', blocks(3669142, True)[3])
    execute('3669142_positive', exe, contains='6.7 5')

    # Input validation and a well-defined default card state.
    compile_case('3669172_before', blocks(3669172)[0])
    for std in ('c++17', 'c++20'):
        exe, _ = compile_case('3669172_after_' + std, blocks(3669172, True)[0], std, True)
        for pos in ('1', '2', '3'):
            execute('3669172_' + std + '_choice_' + pos, exe, data=pos + '\n',
                    contains='Вы выиграли' if pos == '2' else 'Вы проиграли')
        for index, malformed in enumerate(('0\n', '4\n', 'x\n', '')):
            execute('3669172_' + std + '_invalid_' + str(index), exe, data=malformed,
                    expected=1, contains='Ошибка: введите номер позиции от 1 до 3.')
        s = blocks(3669172, True)[0].replace('int main()', 'int sample_main()')
        s += '\nint main(){ card a, b(2, clubs); return a.isEqual(b) ? 0 : 1; }\n'
        exe, _ = compile_case('3669172_default_' + std, s, std, True)
        execute('3669172_default_' + std, exe)

    # Virtual inheritance should not impose an unchecked string-length limit.
    long_name = 'x' * 200
    for corrected in (False, True):
        label = 'after' if corrected else 'before'
        s = blocks(3759850, corrected)[4].replace('int main()', 'int sample_main()')
        s += '\nint main(){ unit_box box("' + long_name + '", 1, "box", 2, "combined", \'p\'); box.print(); }\n'
        exe, _ = compile_case('3759850_long_' + label, s, sanitize=True)
        execute('3759850_long_' + label, exe, expected=0 if corrected else 'failure',
                contains=long_name if corrected else 'AddressSanitizer')
    for std in ('c++17', 'c++20'):
        exe, _ = compile_case('3759850_sample_' + std, blocks(3759850, True)[4], std, True)
        execute('3759850_sample_' + std, exe, contains='PRICE 1010 1010 1010 p')

    # Inherited virtual implementation is usable through an abstract base reference.
    s = '''struct Base { virtual int f() = 0; virtual int g() { return 7; } };
struct Derived : Base { int f() override { return 3; } };
int main(){ Derived d; Base& b = d; return b.f() == 3 && b.g() == 7 ? 0 : 1; }
'''
    exe, _ = compile_case('3759914_inherited_virtual', s)
    execute('3759914_inherited_virtual', exe)

    copy_repro = '''
#include <iostream>
int main(){ RBT<int,int> a; a.add(1,10); a.add(2,20);
    RBT<int,int> b = a; b.add(3,30);
    std::cout << "a.contains(2)=" << a.contains(2) << '\\n';
    std::cout << "b.contains(2)=" << b.contains(2) << '\\n';
    return a.contains(2) ? 0 : 3;
}
'''
    exe, _ = compile_case('3570303_copy_before', rbt() + copy_repro, sanitize=True)
    execute('3570303_copy_before', exe, expected=3, contains='a.contains(2)=0')
    compile_case('3570303_copy_after', rbt(True) + copy_repro, should_compile=False)
    ownership = '''
#include <type_traits>
static_assert(!std::is_copy_constructible_v<RBT<int,int>>);
static_assert(!std::is_copy_assignable_v<RBT<int,int>>);
static_assert(!std::is_move_constructible_v<RBT<int,int>>);
static_assert(!std::is_move_assignable_v<RBT<int,int>>);
int main(){ RBT<int,int> a; a.add(2,20); a[1]=10;
    a.add(2,30); if(a.findValueWithKey(2)!=20) return 1;
    a.remove(99); a.remove(2); if(a.contains(2)) return 2;
    try { (void)a.findValueWithKey(2); return 3; } catch(const std::out_of_range&) {}
    a.clear(); return a.contains(1) ? 4 : 0;
}
'''
    for std in ('c++17', 'c++20'):
        exe, _ = compile_case('3570303_api_after_' + std, rbt(True) + ownership, std, True)
        execute('3570303_api_after_' + std, exe)

    # Verify the already-published nested-owner fix without reporting it as a new defect.
    exe, _ = compile_case('3570166_current_learning_owner', blocks(3570166)[0], sanitize=True)
    execute('3570166_current_learning_owner', exe, contains='42\n0\n2\n0\n')

    # Legal union transitions: built-in scalar assignment vs explicit class construction.
    s = r'''
#include <new>
#include <string>
union U { int i; std::string s; U():i(1){} ~U(){} };
int main() { U u; new (&u.s) std::string("ok");
    if(u.s != "ok") return 1; u.s.~basic_string(); u.i = 7;
    return u.i == 7 ? 0 : 2; }
'''
    exe, _ = compile_case('3212956_explicit_lifetime', s, sanitize=True)
    execute('3212956_explicit_lifetime', exe)


if __name__ == '__main__':
    try:
        main()
    finally:
        (HERE / 'validation_results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print('Passed focused compilation and runtime checks:', len(results))
