#!/usr/bin/env python3
"""Independent checks for the four structurally larger tasks in modules 7--11."""
from collections import Counter
import itertools
import json
from pathlib import Path
import random
from check_task_answers import step

OUT=Path(__file__).parent


def substring_pairs(text):
    # Suffix automaton; each state represents lengths (len(link), len(state)].
    length=[0];link=[-1];nexts=[{}];occ=[0];last=0
    for ch in text:
        cur=len(length)
        length.append(length[last]+1);link.append(0);nexts.append({});occ.append(1)
        p=last
        while p >= 0 and ch not in nexts[p]:
            nexts[p][ch]=cur;p=link[p]
        if p >= 0:
            q=nexts[p][ch]
            if length[p]+1==length[q]:
                link[cur]=q
            else:
                clone=len(length)
                length.append(length[p]+1);link.append(link[q]);nexts.append(nexts[q].copy());occ.append(0)
                while p >= 0 and nexts[p].get(ch)==q:
                    nexts[p][ch]=clone;p=link[p]
                link[q]=link[cur]=clone
        last=cur
    answer=0
    for s in sorted(range(1,len(length)),key=length.__getitem__,reverse=True):
        answer+=(length[s]-length[link[s]])*occ[s]*(occ[s]-1)//2
        occ[link[s]]+=occ[s]
    return answer


def bidecimal(limit):
    tails=[(0,0)]
    ten=two=1
    answer=[]
    while len(answer)<limit:
        candidates=[];new_numbers=[]
        mask=2*two-1
        for dec,binary in tails:
            for d in (0,1):
                a,b=dec+d*ten,binary+d*two
                if a & mask == b:
                    candidates.append((a,b))
                    if d:new_numbers.append(a)
        tails=candidates
        answer.extend(sorted(new_numbers))
        ten*=10;two*=2
    return answer[:limit]


def brute_graph(dataset):
    v=list(map(int,dataset.split()));n,m,k=v[:3]
    successor=[v[3+2*i]-1 for i in range(n)]
    color=[str(v[4+2*i]) for i in range(n)]
    words=[]
    for start in range(n):
        current=start;word=[]
        for _ in range(m):
            word.append(color[current]);current=successor[current]
        words.append(''.join(word))
    return sorted(words)[k-1]


def encode_square(square):
    return '\n'.join(' '.join(map(str,row)) for row in square)


def independent_magic(square):
    n=len(square)
    if any(len(row)!=n for row in square):return False
    if len({x for row in square for x in row})!=n*n:return False
    sums=[sum(row) for row in square]+[sum(row[i] for row in square) for i in range(n)]
    sums+=[sum(square[i][i] for i in range(n)),sum(square[i][n-1-i] for i in range(n))]
    return len(set(sums))==1


def main():
    report={}
    exhaustive=0
    for n in range(1,10):
        for text in map(''.join,itertools.product('ab',repeat=n)):
            frequencies=Counter(text[i:j] for i in range(n) for j in range(i+1,n+1))
            brute=sum(v*(v-1)//2 for v in frequencies.values())
            assert substring_pairs(text)==brute
            exhaustive+=1
    assert substring_pairs('a'*100000)==100001*100000*99999//6
    cases=step(4734985)['source']['test_cases']
    strings=0
    for dataset,expected in cases:
        lines=dataset.split();assert len(lines)-1==int(lines[0])
        actual='\n'.join(str(substring_pairs(s)) for s in lines[1:]);strings+=len(lines)-1
        assert actual==expected.strip()
    report['4734985']={'stored_cases_checked':len(cases),'strings_checked':strings,
                       'independent_exhaustive_binary_strings':exhaustive,
                       'all_equal_boundary_length':100000,'mismatches':0}

    sequence=bidecimal(10000)
    assert sequence==sorted(set(sequence))
    assert all(bin(n)[2:].endswith(str(n)) for n in sequence)
    assert sequence[:6]==[1,10,11,100,101,110]
    for dataset,expected in step(3496826)['source']['test_cases']:
        assert str(sequence[int(dataset)-1])==expected.strip()
    report['3496826']={'stored_cases_checked':len(step(3496826)['source']['test_cases']),
                       'sequence_values_constructed_and_suffix_verified':10000,'mismatches':0}

    ns={};exec(step(4738986)['source']['code'],ns)
    static_cases=step(4738986)['source']['test_cases']
    for dataset,expected in static_cases:
        assert brute_graph(dataset)==expected.strip()==ns['solve'](dataset)
    rng=random.Random(86957)
    for _ in range(60):
        n=rng.randrange(1,10);m=rng.randrange(1,30);k=rng.randrange(1,n+1)
        dataset=f'{n} {m} {k}\n'+'\n'.join(f'{rng.randrange(1,n+1)} {rng.randrange(1,4)}' for _ in range(n))
        assert ns['solve'](dataset)==brute_graph(dataset)
    random.seed(86957)
    generated=ns['generate']()
    for dataset in generated:
        nums=list(map(int,dataset.split()));n,m,k=nums[:3]
        assert 1 <= k <= n <= 100000 and 1 <= m <= 100000
        assert len(nums)==3+2*n
        assert all(1 <= q <= n for q in nums[3::2])
        assert all(1 <= c <= 3 for c in nums[4::2])
    # A maximal chain supplies a closed-form oracle independent of rank doubling.
    dataset=generated[-2]
    n,m,k=map(int,dataset.splitlines()[0].split())
    expected='1'*(n-k)+'2'*(m-(n-k))
    assert ns['solve'](dataset)==expected
    report['4738986']={'stored_cases_bruteforce_checked':len(static_cases),'small_random_graphs_checked':60,
                       'generated_cases_constraints_checked':len(generated),
                       'maximal_chain_checked':{'n':n,'m':m,'k':k},
                       'not_executed':'Full reference solve was not run on the other four generated maximal graphs.',
                       'mismatches':0}

    ns={};exec(step(4927308)['source']['code'],ns)
    fixtures=[[[7]],[[4,9,2],[3,5,7],[8,1,6]],
              [[1,15,14,4],[12,6,7,9],[8,10,11,5],[13,3,2,16]],
              [[35,1,6,26,19,24],[3,32,7,21,23,25],[31,9,2,22,27,20],
               [8,28,33,17,10,15],[30,5,34,12,14,16],[4,36,29,13,18,11]]]
    positive=negative=0
    for matrix in fixtures:
        assert independent_magic(matrix)
        for scale,shift in [(1,0),(-3,7),(10**30, -(10**40))]:
            transformed=[[scale*x+shift for x in row] for row in matrix]
            assert independent_magic(transformed)
            assert ns['check'](encode_square(transformed),len(matrix)) is True
            positive+=1
        if len(matrix)>1:
            bad=[row[:] for row in matrix];bad[0][0]+=1
            assert not independent_magic(bad)
            assert ns['check'](encode_square(bad),len(matrix)) is False
            assert ns['check'](encode_square([[0]*len(matrix) for _ in matrix]),len(matrix)) is False
            negative+=2
        for wrong in ['NO','a','1.5','1 2\n3','']:
            assert ns['check'](wrong,len(matrix)) is False
            negative+=1
    assert ns['check']('NO\n',2) is True;positive+=1
    for wrong in ['no','1 2\n3 4','YES']:
        assert ns['check'](wrong,2) is False;negative+=1
    generated=ns['generate']()
    assert all(int(data)==clue and 1 <= clue <= 1500 for data,clue in generated)
    report['4927308']={'positive_checks':positive,'negative_checks':negative,
                       'orders_with_positive_square_fixtures':[1,3,4,6],
                       'generated_cases_constraints_checked':len(generated),
                       'not_executed':'Large generated square outputs were not constructed/executed; checker logic and distinct sizes were tested directly.',
                       'mismatches':0}
    (OUT/'remaining_task_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
