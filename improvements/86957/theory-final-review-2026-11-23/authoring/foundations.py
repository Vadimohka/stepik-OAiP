#!/usr/bin/env python3
"""Reproduce three prose-only corrections from the pinned effective input."""
from __future__ import annotations

import argparse
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]

EDITS = {
    3177282: [
        (
            'Представляют неотрицательные значения; арифметика идёт по модулю степени двойки. Тип не проверяет, что входные данные были неотрицательными.',
            'Представляют неотрицательные значения. Операции, выполняемые в беззнаковом типе, идут по модулю степени двойки. Тип не проверяет, что входные данные были неотрицательными.',
        ),
        (
            'Для знакового целого выход результата арифметики за представимый диапазон — неопределённое поведение. Беззнаковая арифметика определена по модулю, но её результат тоже может не соответствовать смыслу задачи: вычитание единицы из нуля даёт наибольшее значение типа. Поэтому проверку отрицательного пользовательского ввода удобно делать до преобразования к беззнаковому размеру.',
            'Если целочисленная операция выполняется в знаковом типе, выход результата за его диапазон — неопределённое поведение. Беззнаковая арифметика определена по модулю, но результат тоже может не соответствовать смыслу задачи: <code>0U - 1U</code> даёт наибольшее значение <code>unsigned int</code>. Существенен именно тип вычисления. Малые целочисленные типы перед арифметикой могут преобразовываться: например, <code>unsigned char</code> преобразуется в <code>int</code>, если <code>int</code> вмещает весь его диапазон. Тогда вычитание единицы из такого нулевого значения даёт <code>-1</code> типа <code>int</code>. Правила преобразований разобраны в следующем уроке по ссылке ниже. Проверку отрицательного пользовательского ввода удобно делать до преобразования к беззнаковому размеру.',
        ),
    ],
    3177291: [
        (
            'Для целых частное усекается к нулю: <code>-7 / 2</code> равно −3, <code>-7 % 2</code> равно −1. При представимом частном выполняется равенство <code>(a / b) * b + a % b == a</code>. Делить на ноль нельзя. Также нельзя вычислять частное, не помещающееся в тип: в дополнительном коде это случай минимального знакового значения, делённого на −1.',
            'Для целых частное усекается к нулю: <code>-7 / 2</code> равно −3, <code>-7 % 2</code> равно −1. При ненулевом делителе и представимом частном выполняется равенство <code>(a / b) * b + a % b == a</code>. Нулевой правый операнд запрещён и для <code>/</code>, и для <code>%</code>. Если частное не помещается в тип результата, неопределённое поведение имеют обе операции, даже когда математический остаток равен нулю. Поэтому при представлении знаковых чисел дополнительным кодом нельзя вычислять ни минимальное значение, делённое на <code>-1</code>, ни его остаток от деления на <code>-1</code>. Ненулевого делителя самого по себе недостаточно.',
        ),
    ],
    3177292: [
        (
            'Для положительного, отрицательного числа и нуля выполняется ровно одна ветвь цепочки. При вводе <code>-2</code> вывод равен <code>negative</code>, затем <code>0</code> на новой строке. Неверная запись числа или число вне диапазона <code>int</code> даёт <code>INVALID</code>. Несколько самостоятельных <code>if</code>, напротив, проверялись бы независимо: истинными могут оказаться несколько условий.',
            'Для положительного, отрицательного числа и нуля выполняется ровно одна ветвь цепочки. При вводе <code>-2</code> вывод равен <code>negative</code>, затем <code>0</code> на новой строке. Если прочитать первое целое не удалось — например, получены <code>abc</code>, конец ввода без числа или число вне диапазона <code>int</code>, — программа печатает <code>INVALID</code>. Оператор <code>&gt;&gt;</code> читает числовой префикс: ввод <code>12x</code> даёт число 12, поэтому здесь будут напечатаны <code>positive</code> и <code>1</code> на разных строках. Оставшиеся символы программа не использует; проверку всей строки этот пример не выполняет. Несколько самостоятельных <code>if</code>, напротив, проверялись бы независимо: истинными могут оказаться несколько условий.',
        ),
    ],
}

SUMMARIES = {
    3177282: 'Привязано правило беззнакового переполнения к типу операции; различены 0U - 1U и арифметика unsigned char после целочисленного повышения.',
    3177291: 'Явно распространены ограничения ненулевого делителя и представимости частного на обе операции / и %, включая минимум % -1 при дополнительном коде.',
    3177292: 'Уточнён контракт operator>>: отказ первого чтения целого отделён от принятия числового префикса 12x и игнорирования хвоста.',
}

SECTIONS = {
    3177282: ['basic.fundamental', 'conv.prom'],
    3177291: ['expr.mul'],
    3177292: ['istream.formatted.arithmetic', 'facet.num.get.virtuals'],
}


class PreBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'pre' and self.current is not None:
            self.blocks.append(''.join(self.current))
            self.current = None


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    inputs = json.loads((PACKAGE / 'review_inputs.json').read_text())
    indexed = {row['step_id']: row for row in inputs['steps']}
    outputs = {}
    changes = []
    for sid, replacements in EDITS.items():
        row = indexed[sid]
        source = ROOT / row['effective_path']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == row['file_sha256'], source
        original = json.loads(source.read_text())
        current = copy.deepcopy(original)
        assert original['block']['name'] == 'text'
        text = current['block']['text']
        for old, new in replacements:
            assert text.count(old) == 1, (sid, old)
            text = text.replace(old, new)
        current['block']['text'] = text
        outputs[PACKAGE / row['target_relative_path']] = encode(current)
        if sid in [3177291, 3177292]:
            parser = PreBlocks()
            parser.feed(text)
            filename = 'integer_division.cpp' if sid == 3177291 else 'if_input.cpp'
            outputs[PACKAGE / 'examples/foundations' / filename] = parser.blocks[1].encode('utf-8')
        changes.append({
            'step_id': sid,
            'path': row['target_relative_path'],
            'summary': SUMMARIES[sid],
            'sources': [f'https://timsong-cpp.github.io/cppwp/{version}/{section}'
                        for version in ['n4659', 'n4861'] for section in SECTIONS[sid]],
            'plan': ['VERIFY', 'T2'],
            'previous_effective_path': row['effective_path'],
            'previous_effective_sha256': row['file_sha256'],
        })
    outputs[PACKAGE / 'changes_foundations.json'] = encode(changes)
    # Full historical listings omitted from the old executable suites. Extract
    # them unchanged for this author run; their course payloads are not rewritten.
    for sid, index, filename in [(3177281, 1, 'wide_characters.cpp'),
                                 (3177281, 2, 'narrow_casts.cpp'),
                                 (3177283, 1, 'type_sizes.cpp')]:
        row = indexed[sid]
        source = ROOT / row['effective_path']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == row['file_sha256']
        parser = PreBlocks()
        parser.feed(json.loads(source.read_text())['block']['text'])
        outputs[PACKAGE / 'examples/foundations' / filename] = parser.blocks[index].encode('utf-8')
    for path, data in outputs.items():
        if args.check:
            assert path.read_bytes() == data, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(json.dumps({'status': 'checked' if args.check else 'written',
                      'changed_text_steps': len(changes)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
