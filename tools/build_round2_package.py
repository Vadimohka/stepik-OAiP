"""Attach the second review journal and build an incremental import archive.

Called by build_import_package.py after the cumulative package is built.
The journal stores hashes of the previous published version, so rebuilding
does not need network access or the local Git history.
"""
from __future__ import annotations

import collections
import json
import re
import zipfile
from pathlib import Path

from build_import_package import digest, dump


def write_zip(path, entries, date):
    if len(entries) != len({name for name,_ in entries}):
        raise ValueError(f'Duplicate archive path: {path}')
    stamp=tuple(map(int,date.split('-')))+(0,0,0)
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,content in entries:
            info=zipfile.ZipInfo(name,date_time=stamp)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            archive.writestr(info,content)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None: raise ValueError(f'Corrupt archive: {path}')


def render_value(value):
    if isinstance(value,str): return value
    if isinstance(value,list): return '; '.join(render_value(item) for item in value)
    return json.dumps(value,ensure_ascii=False)


def quoted_value(value):
    """Keep HTML and C++ fragments literal in the Markdown review journal."""
    rendered=render_value(value)
    longest=max((len(match) for match in re.findall(r'`+',rendered)),default=0)
    fence='`'*max(3,longest+1)
    return [fence+'text',rendered,fence]


def augment(root: Path,course_id: int,cumulative_archive: str):
    out=root/'imports'/str(course_id)
    ledger=json.loads((out/'round2_changes.json').read_text())
    steps=ledger['steps']
    baseline=ledger['baseline_step_sha256']
    current={str(p.relative_to(root)):digest(p.read_bytes()) for p in (root/f'courses/{course_id}/steps').glob('*/*.step')}
    if current.keys()!=baseline.keys(): raise ValueError('Round-two baseline file inventory differs from the course')
    revised={path for path in current if current[path]!=baseline[path]}
    if revised!={step['repository_path'] for step in steps}:
        raise ValueError('Round-two journal must be refreshed after editing step files')
    step_by_id={step['step_id']:step for step in steps}
    for step in steps:
        if current[step['repository_path']]!=step['file_sha256']:
            raise ValueError(f"Round-two journal hash is stale: {step['step_id']}")
    findings=ledger['findings']
    if len(findings)!=len({f['id'] for f in findings}): raise ValueError('Duplicate round-two finding ID')
    by_step=collections.defaultdict(list)
    for finding in findings:
        if not finding['step_ids']: raise ValueError(f"Finding has no steps: {finding['id']}")
        for sid in finding['step_ids']:
            if sid not in step_by_id: raise ValueError(f'Finding names an unchanged step: {sid}')
            by_step[sid].append(finding['id'])
    if set(by_step)!=set(step_by_id): raise ValueError('Round-two step changes lack journal entries')
    incremental_name=f'stepik-{course_id}-round2.zip'
    cumulative_name=Path(cumulative_archive).name
    manifest={
        'schema_version':2,'course_id':course_id,'date':ledger['date'],
        'scope':'Only changes since the first published correction package',
        'previous_content_commit':ledger['previous_content_commit'],
        'deployment_status':'pending_user_import','archive':incremental_name,
        'changed_steps':len(steps),'changed_lessons':len({s['lesson_id'] for s in steps}),
        'findings':len(findings),'reviewed_steps':len(ledger['reviewed_step_ids']),
        'steps':steps,
    }
    (out/'round2_manifest.json').write_text(dump(manifest),encoding='utf-8')
    journal=['# Второй проход: внесённые изменения','',
        f"Дата: **{ledger['date']}**. База сравнения: [{ledger['previous_content_commit'][:7]}](https://github.com/Vadimohka/stepik-OAiP/commit/{ledger['previous_content_commit']}).",'',
        f"Повторно просмотрены **{len(ledger['reviewed_step_ids'])} шагов**. Изменены **{len(steps)} шагов** в **{manifest['changed_lessons']} уроках**; журнал содержит **{len(findings)} адресных записей**.",'',
        'Статусы относятся к файлам репозитория. Импорт в Stepik выполняет владелец курса. Правки первого прохода сохранены в отдельном [журнале](changes.md).','',
        '[Новые изменения ZIP](stepik-86957-round2.zip) · [Манифест](round2_manifest.json) · [JSON-журнал](round2_changes.json) · [Протокол проверки задач](validation/round2_code_validation.json)','',
        '## Принятые уточнения условий','',
        'В задачах с недостающими правилами зафиксированы диапазоны входа, порядок вывода и граничные случаи. Они согласованы с исходными тестами и дополнены отдельными тестами. Нестандартная «римская» запись без D сохранена как явно описанное учебное соглашение.','',
        '## Проверка и границы обзора','']
    for line in ledger.get('verification_notes',[]): journal += [str(line),'']
    for finding in sorted(findings,key=lambda f:f['id']):
        kind='Техническое уточнение' if finding['kind']=='technical' else 'Редакторская правка'
        journal += [f"## {finding['id']} · {kind} · {finding['priority']}",'','**Было:**','']
        journal += quoted_value(finding['before'])+['','**Стало:**','']
        journal += quoted_value(finding['after'])+['',
                    '**Почему:** '+render_value(finding['reason']),'',
                    '**Проверка:** '+render_value(finding['validation']),'']
        links=[f"[{sid}](../../{step_by_id[sid]['repository_path']})" for sid in finding['step_ids']]
        journal += ['**Файлы шагов:** '+', '.join(links)+'.','']
        if finding.get('reference_urls'):
            journal += ['**Источники:** '+', '.join(f'[{url}]({url})' for url in dict.fromkeys(finding['reference_urls']))+'.','']
    if ledger.get('deferred'):
        journal += ['## Отдельно отмеченные ограничения','']
        for item in ledger['deferred']: journal += [render_value(item),'']
    journal_text='\n'.join(journal)+'\n'
    (out/'round2_changes.md').write_text(journal_text,encoding='utf-8')

    cumulative=json.loads((out/'manifest.json').read_text())
    cumulative['schema_version']=2
    cumulative['round2']={key:manifest[key] for key in ['date','previous_content_commit','changed_steps','changed_lessons','findings','reviewed_steps']}
    cumulative['round2']['archive']=incremental_name
    for step in cumulative['steps']:
        step['finding_ids']=sorted(set(step.get('finding_ids',[])+by_step.get(step['step_id'],[])))
    (out/'manifest.json').write_text(dump(cumulative),encoding='utf-8')
    readme=(out/'README.md').read_text()
    readme=readme.replace('[Все изменения](changes.md)',
                          '[Первый проход](changes.md) · [Второй проход](round2_changes.md)',1)
    introduction=(
        '## Какой архив выбрать\n\n'
        f'- **Если первый пакет ещё не импортирован:** [{cumulative_name}]({cumulative_name}) — все {cumulative["changed_steps"]} исправленных шагов относительно первоначальной выгрузки.\n'
        f'- **Если пакет из коммита {ledger["previous_content_commit"][:7]} уже импортирован:** [{incremental_name}]({incremental_name}) — только {len(steps)} шагов второго прохода.\n\n'
        f'Второй проход: [журнал](round2_changes.md) · [манифест](round2_manifest.json). '
        'Оба архива содержат текущие полные версии соответствующих `.step`, а не текстовые патчи. Выберите подходящий архив, распакуйте его и импортируйте файлы по урокам.\n\n'
    )
    readme=readme.replace('## Как пользоваться\n',introduction+'## Как пользоваться\n',1)
    (out/'README.md').write_text(readme,encoding='utf-8')

    incremental_readme=[f'# Второй проход курса {course_id}','',
        f'В этом архиве {len(steps)} шагов из {manifest["changed_lessons"]} уроков, изменённых после коммита {ledger["previous_content_commit"][:7]}.','',
        'Этот архив подходит, если первый пакет исправлений уже импортирован. Если нет, используйте полный пакет из репозитория.','',
        '1. Распакуйте архив.','2. Найдите урок по таблице ниже и файлы по исходным ID и позициям.','3. Импортируйте .step в редакторе соответствующего урока, проверьте порядок, содержание и задания перед сохранением.','4. ID внутри .step служит для сопоставления. Этот архив сам по себе не заменяет живые шаги и не переносит прогресс.','',
        '[Версия в репозитории](https://github.com/Vadimohka/stepik-OAiP/tree/main/imports/86957) · [Изменения](round2_changes.md) · [Манифест](round2_manifest.json)','',
        '| Урок | Название | Шагов | Папка |','|---|---|---:|---|']
    grouped=collections.defaultdict(list)
    for step in steps:grouped[(step['module'],step['lesson_number'],step['lesson_id'])].append(step)
    for (module,number,lid),group in grouped.items():
        title=group[0]['lesson_title'].replace('|','\\|')
        incremental_readme.append(f'| {module}.{number} | {title} | {len(group)} | `{module:02}/{number:02}_lesson_{lid}/` |')
    incremental_journal=journal_text
    cumulative_journal=journal_text
    for step in steps:
        target='../../'+step['repository_path']
        incremental_journal=incremental_journal.replace(target,step['archive_path'])
        cumulative_journal=cumulative_journal.replace(target,step['archive_path'])
    incremental_journal=incremental_journal.replace('(changes.md)','(https://github.com/Vadimohka/stepik-OAiP/blob/main/imports/86957/changes.md)')
    incremental_journal=incremental_journal.replace('(stepik-86957-round2.zip)','(https://github.com/Vadimohka/stepik-OAiP/raw/refs/heads/main/imports/86957/stepik-86957-round2.zip)')
    incremental_entries=[('README.md',('\n'.join(incremental_readme)+'\n').encode()),
        ('round2_manifest.json',dump(manifest).encode()),('round2_changes.json',(out/'round2_changes.json').read_bytes()),
        ('round2_changes.md',incremental_journal.encode())]
    incremental_entries += [(s['archive_path'],(root/s['repository_path']).read_bytes()) for s in steps]
    for evidence in sorted((out/'validation').rglob('*')):
        if evidence.is_file() and (evidence.name.startswith('round2_') or 'round2' in evidence.parts) and evidence.suffix in {'.json','.md','.py','.cpp','.c'}:
            incremental_entries.append((str(evidence.relative_to(out)),evidence.read_bytes()))
    write_zip(out/incremental_name,incremental_entries,ledger['date'])

    cumulative_path=root/cumulative_archive
    with zipfile.ZipFile(cumulative_path) as archive:
        entries={name:archive.read(name) for name in archive.namelist()}
    packaged_readme=readme.replace(f'({cumulative_name})','(https://github.com/Vadimohka/stepik-OAiP/tree/main/imports/86957)')
    packaged_readme=packaged_readme.replace(f'({incremental_name})','(https://github.com/Vadimohka/stepik-OAiP/raw/refs/heads/main/imports/86957/'+incremental_name+')')
    entries['README.md']=packaged_readme.encode();entries['manifest.json']=dump(cumulative).encode()
    entries['round2_manifest.json']=dump(manifest).encode()
    entries['round2_changes.json']=(out/'round2_changes.json').read_bytes()
    entries['round2_changes.md']=cumulative_journal.replace(f'({incremental_name})','(https://github.com/Vadimohka/stepik-OAiP/raw/refs/heads/main/imports/86957/'+incremental_name+')').encode()
    write_zip(cumulative_path,list(entries.items()),ledger['date'])
    for archive_path,archive_steps in [(out/incremental_name,steps),(cumulative_path,cumulative['steps'])]:
        with zipfile.ZipFile(archive_path) as archive:
            actual_steps={name for name in archive.namelist() if name.endswith('.step')}
            if actual_steps!={s['archive_path'] for s in archive_steps}:raise ValueError('Unexpected step set in archive')
            for step in archive_steps:
                if digest(archive.read(step['archive_path']))!=step['file_sha256']:raise ValueError('Archive step checksum mismatch')
    return dict(changed_steps=len(steps),changed_lessons=manifest['changed_lessons'],findings=len(findings),
                archive=str((out/incremental_name).relative_to(root)),archive_bytes=(out/incremental_name).stat().st_size,
                archive_sha256=digest((out/incremental_name).read_bytes()),
                cumulative_archive_sha256=digest(cumulative_path.read_bytes()))
