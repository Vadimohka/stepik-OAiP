#!/usr/bin/env python3
"""Independent answer checks for the current module 7--11 snapshot.

Run from the repository root. This script reads course sources, never writes them.
Large hidden inputs/outputs are deliberately omitted from the report.
"""
from collections import Counter
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).parent


def step(sid):
    path = next((ROOT / 'courses/86957/steps').rglob(f'*_{sid}_*.step'))
    return json.loads(path.read_text())['block']


def last_nonzero_sum(n):
    total = 0
    while n > 0:
        q, r = divmod(n, 10)
        total += 45 * q + r * (r + 1) // 2
        n = q
    return total


def odd_divisor_sum(n):
    total = 0
    while n:
        total += ((n + 1) // 2) ** 2
        n //= 2
    return total


def remove_digit(s):
    cut = next((i for i in range(len(s)-1) if s[i] < s[i+1]), len(s)-1)
    return (s[:cut] + s[cut+1:]).lstrip('0') or '0'


def power_tail(n, m):
    # Saturating exponentiation independently decides whether padding is needed.
    cap, value, base, exp = 10**10, 1, n, m
    while exp:
        if exp & 1:
            value = min(cap, value * base)
        base = min(cap, base * base)
        exp //= 2
    residue = pow(n, m, cap)
    return str(residue) if value < cap else f'{residue:010d}'


def reconstruction(L, modulus, a, b):
    if len(a) > L or len(b) > L:
        return 0

    def count(placements):
        fixed = {}
        for at, text in placements:
            for i, c in enumerate(text, at):
                if i in fixed and fixed[i] != c:
                    return 0
                fixed[i] = c
        return pow(26, L - len(fixed), modulus)

    first = [(0, a), (L-len(b), b)]
    second = [(0, b), (L-len(a), a)]
    return (count(first) + count(second) - count(first+second)) % modulus


def chip(s, t):
    states = {(i, False) for i, ch in enumerate(s) if ch == t[0]}
    for ch in t[1:]:
        nxt = set()
        for i, turned in states:
            if not turned and i+1 < len(s) and s[i+1] == ch:
                nxt.add((i+1, False))
            if i > 0 and s[i-1] == ch:
                nxt.add((i-1, True))
        states = nxt
        if not states:
            return 'NO'
    return 'YES' if states else 'NO'


def roman(n):
    hundreds = ['', 'C', 'CC', 'CCC', 'CCCC', 'CCCCC', 'CCCCM', 'CCCM', 'CCM', 'CM']
    tens = ['', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC']
    ones = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX']
    return 'M' * (n//1000) + hundreds[n//100%10] + tens[n//10%10] + ones[n%10]


def bijective_ternary(n):
    out = ''
    while n:
        n, r = divmod(n-1, 3)
        out = str(r+1) + out
    return out


def reform(text):
    text = ''.join(ch for ch in text if ch not in 'CQWX')
    replacements = {'ph':'f', 'th':'z', 'ee':'i', 'qu':'kv', 'you':'u', 'oo':'u'}
    out, i = [], 0
    while i < len(text):
        width = next((w for w in (3, 2) if text[i:i+w].lower() in replacements), 0)
        if width:
            token = replacements[text[i:i+width].lower()]
            if text[i].isupper():
                token = token[0].upper() + token[1:]
            out.append(token)
            i += width
        else:
            out.append(text[i])
            i += 1
    text = ''.join(out)
    out = []
    for ch in text:
        token = {'q':'k', 'x':'ks', 'w':'v'}.get(ch.lower(), ch)
        if ch.isupper():
            token = token[0].upper() + token[1:]
        out.append(token)
    text = ''.join(out)
    out = []
    for i, ch in enumerate(text):
        if ch.lower() == 'c':
            token = 's' if i+1 < len(text) and text[i+1].lower() in 'eiy' else 'k'
            ch = token.upper() if ch.isupper() else token
        out.append(ch)
    text = ''.join(out)
    out = []
    for ch in text:
        is_consonant = ch.lower() in 'bcdfghjklmnpqrstvwxz'
        if not (is_consonant and out and out[-1].lower() == ch.lower()):
            out.append(ch)
    return ''.join(out)


def solve(sid, dataset):
    tokens = dataset.split()
    ints = None
    if sid in (4700299, 3428206, 3428255, 3384518, 5828883, 4739135, 3253164, 3496771, 3496704, 3496878):
        ints = list(map(int, tokens))
    if sid == 4700299:
        return '1.' + '9' * (ints[0]-1) + '8'
    if sid == 3428206:
        pairs = list(zip(ints[::2], ints[1::2]))
        assert pairs[-1][0] < 0 and pairs[-1][1] < 0
        assert all(0 <= p <= q <= 2147483647 for p, q in pairs[:-1])
        return '\n'.join(str(last_nonzero_sum(q)-last_nonzero_sum(p-1)) for p, q in pairs[:-1])
    if sid == 3428255:
        triples = list(zip(ints[::3], ints[1::3], ints[2::3]))
        assert triples[-1] == (0, 0, 0)
        assert all(0 < k < 10**19 and 0 < n < 10**19 and 0 < t < 10 for k, n, t in triples[:-1])
        return '\n'.join(f'Case #{i}: {pow(k,n,10**t)}' for i, (k,n,t) in enumerate(triples[:-1],1))
    if sid == 3384518:
        assert len(ints)-1 == ints[0]
        assert 1 <= ints[0] <= 1000 and all(1 <= n <= 2147483647 for n in ints[1:])
        return '\n'.join(str(odd_divisor_sum(n)) for n in ints[1:])
    if sid == 5828883:
        it = iter(ints)
        total = next(it)
        out = []
        count = 0
        for _ in range(total):
            n = next(it); count += n
            left = [next(it) for _ in range(n)]
            right = [next(it) for _ in range(n)]
            value = 1
            for i, (l, r) in enumerate(zip(left, right), 1):
                assert 1 <= l <= 10**9 and 1 <= r <= 10**9
                value = value * max(0, r//i - (l-1)//i) % 1000000007
            out.append(str(value))
        assert next(it, None) is None and 1 <= total <= 10**5 and count <= 10**5
        return '\n'.join(out)
    if sid == 5822035:
        assert len(tokens)-1 == int(tokens[0])
        assert sum(map(len,tokens[1:])) <= 10**5
        return '\n'.join(remove_digit(s) for s in tokens[1:])
    if sid == 4739135:
        assert len(ints)-1 == 2*ints[0] and 1 <= ints[0] <= 10
        assert all(0 <= n <= 10**9 for n in ints[1:])
        return '\n'.join(power_tail(n,m) for n,m in zip(ints[1::2],ints[2::2]))
    if sid == 3253164:
        assert len(ints)==1 and 1 <= ints[0] <= 10**9
        return str((ints[0]+1)//10)
    if sid == 3446015:
        assert len(tokens)==1 and 1 <= len(tokens[0]) <= 14
        freq = Counter(tokens[0])
        return str(math.factorial(len(tokens[0])) // math.prod(math.factorial(v) for v in freq.values()))
    if sid == 3446002:
        assert (len(tokens)-1) == 4*int(tokens[0])
        out = []
        for i in range(1,len(tokens),4):
            L,m = map(int,tokens[i:i+2]);a,b=tokens[i+2:i+4]
            assert 1 <= L <= 10**9 and 1 <= m <= 10**4 and 1 <= len(a) <= 200 and 1 <= len(b) <= 200
            out.append(str(reconstruction(L,m,a,b)))
        return '\n'.join(out)
    if sid == 3446094:
        assert len(tokens)==1 and 1 <= len(tokens[0]) <= 10**5
        s=tokens[0]
        return str(-1 if len(set(s))==1 else len(s)-int(s==s[::-1]))
    if sid == 3446132:
        assert len(tokens)-1 == 2*int(tokens[0])
        pairs=list(zip(tokens[1::2],tokens[2::2]))
        assert sum(len(s) for s,t in pairs) <= 500
        assert all(1 <= len(s) <= 500 and 1 <= len(t) <= 2*len(s)-1 for s,t in pairs)
        return '\n'.join(chip(s,t) for s,t in pairs)
    if sid == 4949336:
        return reform(dataset.rstrip('\r\n'))
    if sid == 3496771:
        assert len(ints)==1 and 1 <= ints[0] <= 3999
        return roman(ints[0])
    if sid == 3496704:
        assert len(ints)-1 == ints[0] and 1 <= ints[0] <= 1000
        assert all(1 <= n <= 10**9 for n in ints[1:])
        return '\n'.join(str((n+1)//10) for n in ints[1:])
    if sid == 3496878:
        assert len(ints)==1 and 1 <= ints[0] <= 2*10**9
        return bijective_ternary(ints[0])
    raise ValueError(sid)


def self_checks():
    for n in range(10000):
        if n==0:
            last=odd=0
        else:
            k=n
            while k%10==0:k//=10
            last += k%10
            k=n
            while k%2==0:k//=2
            odd += k
        assert last_nonzero_sum(n)==last
        assert odd_divisor_sum(n)==odd
        assert remove_digit(str(n))==str(max((int(str(n)[:i]+str(n)[i+1:] or '0') for i in range(len(str(n))))))
    for n in range(30):
        for m in range(40):
            exact=str(n**m)
            assert power_tail(n,m)==exact[-10:]
    # Independent recurrence f(n,r), sum over r, from the image in 3428255.
    for k in range(1,7):
        row=[1]
        for n in range(1,8):
            row=[sum(row[r-i] for i in range(k) if 0 <= r-i < len(row)) for r in range(n*(k-1)+1)]
            assert sum(row)==k**n
    # Exhaustive anagram sets on a small alphabet.
    for n in range(1,7):
        for chars in itertools.product('ab',repeat=n):
            word=''.join(chars)
            assert int(solve(3446015,word))==len(set(itertools.permutations(word)))
    # Finite direct enumeration of all written chip routes.
    for n in range(1,7):
        for tup in itertools.product('ab',repeat=n):
            s=''.join(tup)
            routes=set()
            for start in range(n):
                for right in range(n-start):
                    for left in range(start+right+1):
                        positions=list(range(start,start+right+1))+list(range(start+right-1,start+right-left-1,-1))
                        routes.add(''.join(s[p] for p in positions))
            for m in range(1,min(2*n,8)):
                for t in map(''.join,itertools.product('ab',repeat=m)):
                    assert (chip(s,t)=='YES')==(t in routes)
    for n in range(1,10000):
        v=0
        for ch in bijective_ternary(n):v=3*v+int(ch)
        assert v==n
    return {'last_nonzero_and_odd_divisor_n':10000,'delete_digit_n':10000,'power_small_cases':1200,
            'image_recurrence_cases':42,'anagram_binary_max_length':6,
            'chip_exhaustive_source_max_length':6,'chip_exhaustive_target_max_length':7,
            'bijective_ternary_roundtrips':9999}


def main():
    self_report=self_checks()
    ids=[4700299,3428206,3428255,3384518,5828883,5822035,4739135,3253164,3446015,3446002,3446094,3446132,4949336,3496771,3496704,3496878]
    results=[]
    for sid in ids:
        block=step(sid)
        cases=block['source']['test_cases']
        mismatches=[]
        for num,(dataset,expected) in enumerate(cases,1):
            answer=solve(sid,dataset)
            if answer.rstrip('\r\n') != expected.rstrip('\r\n'):
                mismatches.append({'case':num,'input_length':len(dataset),'first_different_offset':next((i for i,(a,b) in enumerate(zip(answer,expected)) if a!=b), min(len(answer),len(expected))), 'expected_preview':expected[:120],'actual_preview':answer[:120]})
        results.append({'step_id':sid,'stored_cases_checked':len(cases),'mismatches':mismatches})
    report={'snapshot':'d936c0ee8d9f720ba26fec1b109a1153ae3b5930','self_checks':self_report,'results':results}
    (OUT/'task_answer_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
