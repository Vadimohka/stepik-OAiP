"""Stepik source.code for step 4734985. No network or file access.

Only generate/solve/check are Stepik entry points. case_specs is also used by
the local verifier to attach human-readable names to the generated test pairs.
"""

import re


def _dataset(records):
    return str(len(records)) + "\n" + "".join(
        "{} {}\n".format(priority, label) for priority, label in records
    )


def _numbers(seed):
    # An explicit recurrence keeps the fixtures independent of random versions.
    while True:
        seed = (1664525 * seed + 1013904223) % 4294967296
        yield seed


def case_specs():
    # The first case is the one displayed sample (samples_count remains 1).
    yield "sample_stability", _dataset([
        (2, 30), (1, 9), (2, 10), (1, 4), (2, 30), (0, 8)
    ]), ["sample", "equal_keys", "duplicate_record", "not_label_order"]
    yield "empty", _dataset([]), ["empty"]
    yield "one_zero", _dataset([(0, 0)]), ["singleton", "zero"]
    yield "one_negative", _dataset([(-1000000000, -1000000000)]), ["bounds"]
    yield "equal_keys", _dataset([(7, 90), (7, -3), (7, 90), (7, 4)]), [
        "equal_keys", "duplicate_record", "not_label_order"
    ]
    yield "identical_records", _dataset([(4, 5)] * 8), ["duplicate_record"]
    yield "reverse_two", _dataset([(2, 7), (-2, 8)]), ["reverse", "negative"]
    yield "already_sorted", _dataset([
        (-2, 8), (-2, 3), (0, 0), (3, 17), (3, 5)
    ]), ["sorted", "equal_keys"]
    yield "interleaved_groups", _dataset([
        (3, 5), (1, 8), (3, 4), (2, 9), (1, 7), (2, 1), (3, 6)
    ]), ["equal_keys", "interleaved"]
    yield "signed_bounds", _dataset([
        (1000000000, -1000000000), (-1000000000, 1000000000),
        (0, -1), (-1000000000, -1000000000), (1000000000, 0)
    ]), ["bounds", "negative", "equal_keys"]
    yield "same_labels_different_keys", _dataset([
        (5, 4), (-1, 4), (5, 4), (0, 4), (-1, 4)
    ]), ["same_labels", "duplicate_record"]
    for n in (2, 3, 5, 16, 31, 64, 101, 257, 1000):
        numbers = _numbers(4734985 + n)
        records = [(next(numbers) % 13 - 6, next(numbers) % 29 - 14)
                   for _ in range(n)]
        yield "generated_{}".format(n), _dataset(records), [
            "deterministic_generated", "equal_keys", "negative"
        ]
    yield "max_reverse", _dataset([
        (100000 - i, -i) for i in range(100000)
    ]), ["max_n", "reverse"]
    yield "max_equal", _dataset([
        (1, 100000 - i) for i in range(100000)
    ]), ["max_n", "equal_keys", "not_label_order"]
    numbers = _numbers(869574734)
    yield "max_mixed", _dataset([
        (next(numbers) % 1009 - 504, next(numbers) % 2001 - 1000)
        for _ in range(100000)
    ]), ["max_n", "equal_keys", "negative", "deterministic_generated"]


def solve(dataset):
    values = list(map(int, dataset.split()))
    n = values[0]
    assert 0 <= n <= 100000 and len(values) == 1 + 2 * n
    records = list(zip(values[1::2], values[2::2]))
    assert all(-1000000000 <= value <= 1000000000
               for record in records for value in record)
    # Explicit original position makes the required tie-break visible.
    indexed = list(enumerate(records))
    indexed.sort(key=lambda item: (item[1][0], item[0]))
    return "".join("{} {}\n".format(*record) for _, record in indexed)


def generate():
    return [(dataset, solve(dataset)) for _, dataset, _ in case_specs()]


def check(reply, clue):
    actual = reply.split()
    expected = clue.split()
    if len(actual) != len(expected):
        return False
    for got, wanted in zip(actual, expected):
        if re.fullmatch(r"[+-]?[0-9]+", got) is None:
            return False
        try:
            if int(got) != int(wanted):
                return False
        except ValueError:
            return False
    return True
