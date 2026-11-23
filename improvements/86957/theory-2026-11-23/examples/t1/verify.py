#!/usr/bin/env python3
"""Compile exact introductory examples, including the explained negative case."""
from pathlib import Path
import hashlib,html,json,os,re,shutil,subprocess,tempfile

HERE=Path(__file__).resolve().parent
PKG=HERE.parents[1]
REPORT=HERE/'validation.json'
def write(data): REPORT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def blocks(sid):
    p=next((PKG/'steps').glob(f'*/*_{sid}_text.step'))
    return [(m[0],html.unescape(m[1])) for m in re.findall(r'<pre><code(?: class="language-([^"]+)")?>(.*?)</code></pre>',json.loads(p.read_bytes())['block']['text'],re.S)]
def run(args,**kw):return subprocess.run(list(map(str,args)),text=True,capture_output=True,timeout=60,**kw)
def main():
    report={'status':'running','all_passed':False,'scope':'Author checks of complete theory illustrations, no learner tasks','counts':{'compilations':0,'runtime_cases':0,'expected_compile_failures':0,'cmake_configurations':0},'input_sha256':{}}
    write(report)
    try:
        inputs=[Path(__file__),PKG/'changes_t1.json']+[PKG/x['path'] for x in json.loads((PKG/'changes_t1.json').read_bytes())]
        report['input_sha256']={p.relative_to(PKG).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
        report['compiler']=run(['g++','--version']).stdout.splitlines()[0]
        with tempfile.TemporaryDirectory(prefix='theory-t1-') as td:
            folder=Path(td)
            for sid,expected in [(3201305,'250\n'),(3201179,'Hello, C++!\n'),(3231317,'Hello C++\n')]:
                code=next(b for lang,b in blocks(sid) if lang=='cpp')
                source=folder/f'{sid}.cpp';source.write_text(code)
                for std in ['c++17','c++20']:
                    binary=folder/f'{sid}-{std}'
                    c=run(['g++',f'-std={std}','-Wall','-Wextra','-Wpedantic','-Werror',source,'-o',binary]);assert c.returncode==0,c.stderr
                    report['counts']['compilations']+=1
                    r=run([binary]);assert (r.returncode,r.stdout,r.stderr)==(0,expected,''),(sid,r.stdout,r.stderr)
                    report['counts']['runtime_cases']+=1
            source=folder/'negative.cpp';source.write_text(next(b for lang,b in blocks(3201189) if lang=='cpp'))
            for std in ['c++17','c++20']:
                r=run(['g++',f'-std={std}',source,'-o',folder/'negative']);assert r.returncode!=0 and 'cout' in r.stderr
                report['counts']['expected_compile_failures']+=1
            cmake=os.environ.get('CMAKE') or shutil.which('cmake');assert cmake,'CMake is required (or set CMAKE)'
            cmake_text=next(b for lang,b in blocks(3231317) if lang=='cmake')
            (folder/'CMakeLists.txt').write_text(cmake_text)
            (folder/'main.cpp').write_text(next(b for lang,b in blocks(3231317) if lang=='cpp'))
            for args in [[cmake,'-S',folder,'-B',folder/'build','-DCMAKE_BUILD_TYPE=Debug'],[cmake,'--build',folder/'build']]:
                r=run(args);assert r.returncode==0,r.stderr
            r=run([folder/'build/hello']);assert (r.returncode,r.stdout)==(0,'Hello C++\n')
            report['counts']['cmake_configurations']+=1;report['counts']['runtime_cases']+=1
        assert report['input_sha256']=={p.relative_to(PKG).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
        report.update(status='passed',all_passed=True,limitations=['Windows/MSVC and macOS were not executed.'])
        write(report);print(json.dumps({'status':report['status'],'counts':report['counts']}));return 0
    except Exception as error:
        report.update(status='failed',all_passed=False,error=f'{type(error).__name__}: {error}');write(report);print(report['error']);return 1
if __name__=='__main__':raise SystemExit(main())
