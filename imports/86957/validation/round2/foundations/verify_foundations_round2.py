#!/usr/bin/env python3
"""Addressed checks for the second editorial pass; no course files are written."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


WORK = Path(__file__).resolve().parent
BASELINE_REVISION = '8bf4639ce2799a13146e22ed13cf103dd1916ad5'


def find_repo():
    for parent in Path(__file__).resolve().parents:
        if (parent / 'courses/86957/steps').is_dir():
            return parent
    raise SystemExit('Cannot locate courses/86957/steps among the script parents; use --repo.')


ap = argparse.ArgumentParser()
ap.add_argument('--repo', type=Path)
ap.add_argument('--log', type=Path, default=WORK / 'foundations.json')
ap.add_argument('--out', type=Path, default=WORK / 'foundations_validation.json')
args = ap.parse_args()
args.repo = (args.repo or find_repo()).resolve()
artifacts = WORK / 'cpp'
artifacts.mkdir(parents=True, exist_ok=True)
build = tempfile.TemporaryDirectory(prefix='build-', dir=WORK)
build_dir = Path(build.name)
log = json.loads(args.log.read_text())
paths = {int(p.name.split('_')[1]): p.relative_to(args.repo)
         for p in (args.repo / 'courses/86957/steps').glob('*/*.step')}
baseline = []
for sid in log['reviewed_step_ids']:
    relative = paths[sid]
    command = ['git', '-C', str(args.repo), 'show', f'{BASELINE_REVISION}:{relative.as_posix()}']
    proc = subprocess.run(command, capture_output=True, text=True, timeout=10)
    if proc.returncode:
        raise SystemExit('The baseline Git revision is unavailable. Use a full clone containing '
                         + BASELINE_REVISION + '. No fetch or repository modification is performed.')
    baseline.append({'id': sid, 'path': relative, 'data': json.loads(proc.stdout)})
old = {r['id']:r for r in baseline}
current = {r['id']:json.loads((args.repo / r['path']).read_text()) for r in baseline}
changed = {sid for f in log['findings'] for sid in f['step_ids']}
checks = []


def check(name, condition, details=None):
    checks.append({'name':name, 'passed':bool(condition), 'details':details})
    if not condition:
        raise AssertionError((name, details))


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag not in {'img','br','hr','meta','link','input','source','wbr','embed','area','base','col','param','track'}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append((tag, self.stack[-1] if self.stack else None))
            if tag in self.stack:
                del self.stack[len(self.stack) - 1 - self.stack[::-1].index(tag):]


def tags(s):
    p = Tags()
    p.feed(s)
    p.close()
    return p


check('complete_review', set(log['reviewed_step_ids']) == set(old) and len(old) == 173)
check('owned_steps_are_non_code', all(current[s]['block']['name'] != 'code' for s in changed), sorted(changed))
check('identity_type_time', all(
    current[s]['id'] == r['data']['id'] and current[s]['time'] == r['data']['time']
    and current[s]['block']['name'] == r['data']['block']['name']
    for s,r in old.items()))
actual_noncode_changes = {s for s,r in old.items() if current[s]['block']['name'] != 'code' and current[s] != r['data']}
check('log_matches_owned_diff', actual_noncode_changes == changed,
      {'logged':len(changed),'actual':len(actual_noncode_changes)})
media_counts = Counter()
html_baseline_exceptions = []
choice_count = 0
for sid in sorted(changed):
    a = old[sid]['data']['block']; b = current[sid]['block']
    for tag in ('img','video','iframe'):
        pattern = r'<' + tag + r'\b[^>]*>'
        av = re.findall(pattern,a['text']); bv = re.findall(pattern,b['text'])
        assert av == bv, (sid,tag)
        media_counts[tag] += len(av)
    assert a.get('video') == b.get('video'), sid
    # Preserve video links as well as embedded elements.
    video_links = lambda t: [x for x in re.findall(r'href="([^"]+)"',t)
                             if any(k in x.lower() for k in ('youtube','youtu.be','vimeo','.mp4'))]
    assert video_links(a['text']) == video_links(b['text']), sid
    before, after = tags(a['text']), tags(b['text'])
    assert set(after.tags) <= set(before.tags) | {'p','code','strong','sup','sub','br'}, (sid,'new HTML tags')
    assert len(after.errors) + len(after.stack) <= len(before.errors) + len(before.stack), (sid,'HTML structure')
    if after.errors or after.stack:
        html_baseline_exceptions.append({'step_id':sid, 'existing_errors':after.errors,'existing_unclosed_tags':after.stack})
    if b['name'] == 'choice':
        choice_count += 1
        src = b['source']
        assert [x['is_correct'] for x in src['options']] == [x['is_correct'] for x in a['source']['options']], sid
        assert src['is_multiple_choice'] == b['options']['is_multiple_choice'], sid
        correct = sum(x['is_correct'] for x in src['options'])
        assert correct >= 1 and (src['is_multiple_choice'] or correct == 1), sid
        assert src['sample_size'] <= len(src['options']), sid
        for ao, bo in zip(a['source']['options'], src['options']):
            if src.get('is_html_enabled'):
                for field in ('text','feedback'):
                    if ao[field] != bo[field]:
                        assert not tags(bo[field]).tags, (sid,'new option markup',field)
    if b['name'] == 'table':
        assert len(b['source']['rows']) == len(a['source']['rows']) == 20
        assert len(b['source']['columns']) == len(a['source']['columns']) == 5
        assert [r['columns'] for r in a['source']['rows']] == [r['columns'] for r in b['source']['rows']]
check('media_preserved', True, dict(media_counts))
check('html_no_added_structure_errors', True, html_baseline_exceptions)
check('choice_keys_and_table_keys_preserved', True, {'choice_steps':choice_count,'table_steps':1})

check('exact_hex_fraction', Fraction(3,16)+Fraction(15,256)+Fraction(5,4096) == Fraction('0.247314453125'))
check('exact_octal_fraction', Fraction(5,8)+Fraction(2,64)+Fraction(4,512) == Fraction('0.6640625'))


def fraction_digits(x, base, count):
    out = ''
    for _ in range(count):
        x *= base
        digit = x.numerator // x.denominator
        out += '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[digit]
        x -= digit
    return out


check('reverse_truncated_fractions',
      fraction_digits(Fraction('0.24731'),16,4) == '3F4F'
      and fraction_digits(Fraction('0.6640'),8,4) == '5237')
base_keys = []
for item in current[3261481]['block']['source']['options']:
    digits, base = re.fullmatch(r'(\w+)\s+\((\d+)\)',html.unescape(item['text'])).groups()
    value = int(digits,int(base))
    base_keys.append({'representation':item['text'],'value':value,'correct':value == 71356825739579})
    assert (value == 71356825739579) == item['is_correct']
check('base_conversion_all_12_keys', len(base_keys)==12, base_keys)
check('decimal_complement', (10000-386)==9614 and (119+9614)==9733 and (10000-9733)==267)

compiler = shutil.which('g++')
assert compiler, 'g++ is required for the addressed C++ checks'
compiler_version = subprocess.run([compiler,'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]


def compile_source(name, source, standard='c++17', expect_success=True):
    src = artifacts / (name + '.cpp')
    exe = build_dir / name
    src.write_text(source + '\n')
    command = ['g++', '-std='+standard, '-Wall','-Wextra','-pedantic',
               str(src.relative_to(WORK)), '-o', str(exe.relative_to(WORK))]
    proc = subprocess.run(command,cwd=WORK,capture_output=True,text=True,timeout=30)
    check('compile_'+name,(proc.returncode==0)==expect_success,
          {'command':command,'returncode':proc.returncode,'stderr':proc.stderr,
           'source_sha256':hashlib.sha256(source.encode()).hexdigest()})
    return exe


def run(exe, data='', expected=None, status=0, contains=None):
    proc = subprocess.run([str(exe)],input=data,capture_output=True,text=True,timeout=5)
    check('run_'+exe.name,proc.returncode==status and (expected is None or proc.stdout==expected)
          and (contains is None or contains in proc.stdout),
          {'input':data,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})


def cpp_programs(sid):
    blocks = re.findall(r'<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>',current[sid]['block']['text'],re.S)
    return [html.unescape(x).replace('\xa0',' ') for x in blocks if '#include' in x and 'int main' in x]


# These specific examples were read in full; they only use standard console I/O.
io = cpp_programs(3215075)
check('input_output_examples_count',len(io)==3)
for n,source in enumerate(io):
    exe = compile_source(f'io_{n}',source)
    if n == 0:
        run(exe,expected='Name: Tom\nAge: 33\nWeight: 81.23\n')
    else:
        run(exe,'21 70.5\n',contains='Your age: 21\t your weight: 70.5\n')
        run(exe,'bad\n',status=1)
        run(exe,'21 bad\n',status=1)

conditions = cpp_programs(3177292)
check('if_examples_count',len(conditions)==4)
outputs = ['x is greater than 50\nEnd of Program\n','x is less or equal 60 \n','x is equal 60 \n']
for n,source in enumerate(conditions):
    exe = compile_source(f'condition_{n}',source)
    if n<3:
        run(exe,expected=outputs[n])
    else:
        run(exe,'+\n',contains='Результат: 8\n')
        run(exe,'-\n',contains='Результат: 2\n')
        run(exe,'',status=1)

types_source = r'''#include <cassert>
#include <limits>
#include <type_traits>
static_assert(std::is_same_v<decltype('a'), char>);
static_assert(std::is_same_v<decltype(42), int>);
static_assert(std::is_same_v<decltype(1234567890L), long>);
static_assert(std::is_same_v<decltype(1703U), unsigned int>);
static_assert(std::is_same_v<decltype(2128506UL), unsigned long>);
static_assert(std::is_same_v<decltype(3.14), double>);
static_assert(std::is_same_v<decltype(!0x0), bool>);
static_assert(std::is_same_v<decltype(false & true), int>);
static_assert(std::is_same_v<decltype(false && true), bool>);
int main() {
    assert(14/3 == 4 && !0x0);
    assert(!(false & true) && !(false && true));
    assert((2 << 2) == 8 && (16 >> 3) == 2 && ~9 == -10);
    for (int state=0; state<4; ++state) {
        const int online=1, offline=2;
        int status=state;
        status |= online;
        assert((status & online) && ((status & offline) == (state & offline)));
        status = online;
        if (state & offline) assert((status & offline) != (state & offline));
    }
    static_assert(std::numeric_limits<double>::radix == 2);
    static_assert(std::numeric_limits<double>::digits == 53);
    long long integer=9007199254740993LL;
    double rounded=static_cast<double>(integer);
    assert(static_cast<long long>(rounded) != integer);
}'''
run(compile_source('literal_bit_and_flag_rules',types_source,'c++20'))

constructor = r'''#include <cassert>
int initialized = 0;
__attribute__((constructor)) void prepare() { initialized=42; }
int main() { assert(initialized==42); }'''
run(compile_source('gcc_constructor',constructor))
goto_good = r'''#include <cassert>
int destroyed=0;
struct Guard { ~Guard() { ++destroyed; } };
int main() {
    { Guard guard; goto after; }
after:
    assert(destroyed==1);
    int x=1;
loop1:
    x++;
    if (x<=100) goto loop1;
    assert(x==101);
}'''
run(compile_source('goto_destruction_and_counter',goto_good))
compile_source('goto_crosses_initializer','int main() { goto after; int n=1; after: return n; }',expect_success=False)
void_return = 'void action() {} void forward() { return action(); } int main() { forward(); }'
run(compile_source('void_return_expression',void_return))

# Diagnose invalid examples without executing undefined behaviour.
compile_source('syntax_error_8268748','int main() { int a=1; if(a +) {} }',expect_success=False)
compile_source('literal_error_8268748','int main() { int x=1; x = 1e+; }',expect_success=False)
compile_source('name_error_8268748','int main() { int a=1; a = b + 1; }',expect_success=False)

report = {'status':'passed','scope':{'modules':[1,2,3,4],'reviewed_steps':len(old),'changed_steps':len(changed)},
          'baseline_revision':BASELINE_REVISION,
          'compiler':compiler_version,'checks':checks,
          'limits':['Video/audio content was not transcribed or re-reviewed.',
                    'Code tasks belong to the root agent and are excluded from these edits.',
                    'The numeric-conversion counterexample explicitly checks the local binary64 assumptions.',
                    'Invalid C++ examples are compiled only; undefined behaviour is not executed.']}
args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
build.cleanup()
print(json.dumps({'status':'passed','checks':len(checks),'changed_steps':len(changed),'report':args.out.name},ensure_ascii=False))
