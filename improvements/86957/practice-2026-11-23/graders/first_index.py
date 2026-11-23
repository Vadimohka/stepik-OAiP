"""Stepik source.code for step 3496826. Deterministic generate/solve/check.

case_specs is a local helper, not an additional Stepik API entry point.
"""

import re


def _dataset(values, queries):
    return "{} {}\n{}\n{}\n".format(
        len(values), len(queries),
        " ".join(map(str, values)), " ".join(map(str, queries))
    )


def _numbers(seed):
    while True:
        seed = (1664525 * seed + 1013904223) % 4294967296
        yield seed


def case_specs():
    # These three cases are the displayed samples (samples_count remains 3).
    yield "sample_duplicates", _dataset(
        [-3, 1, 1, 1, 7, 9], [1, 9, -3, 2, 10]
    ), ["sample", "duplicates", "first_index", "missing", "zero_index"]
    yield "sample_empty", _dataset([], [-1, 0, 5]), ["sample", "empty"]
    yield "sample_singleton", _dataset([4], [4, 3, 5, 4]), [
        "sample", "singleton", "missing", "repeated_queries"
    ]
    yield "empty_no_queries", _dataset([], []), ["empty", "zero_queries"]
    yield "nonempty_no_queries", _dataset([-2, 0, 0, 9], []), ["zero_queries"]
    yield "all_equal", _dataset([5] * 9, [5, 4, 6, 5]), [
        "duplicates", "first_index", "missing"
    ]
    yield "missing_gaps", _dataset([-10, -4, 0, 6, 12], [-11, -8, -1, 3, 11, 13]), [
        "missing", "negative", "gaps"
    ]
    yield "both_ends_duplicates", _dataset(
        [-7, -7, -7, 0, 1, 9, 9], [9, -7, 1, 0, -8, 10]
    ), ["duplicates", "first_index", "ends"]
    yield "signed_bounds", _dataset(
        [-1000000000, -1000000000, 0, 1000000000, 1000000000],
        [-1000000000, 1000000000, -999999999, 999999999, 0]
    ), ["bounds", "duplicates", "missing"]
    yield "length_two", _dataset([-1, 1], [-1, 1, 0, -2, 2]), ["two_elements"]
    for n in (3, 5, 16, 31, 64, 101, 257, 1000):
        numbers = _numbers(3496826 + n)
        values = sorted(next(numbers) % 201 - 100 for _ in range(n))
        queries = [next(numbers) % 301 - 150 for _ in range(2 * n)]
        queries.extend((values[0], values[-1]))
        yield "generated_{}".format(n), _dataset(values, queries), [
            "deterministic_generated", "duplicates", "missing", "negative"
        ]
    yield "max_empty_queries", _dataset([], [0] * 100000), ["empty", "max_q"]
    yield "max_equal", _dataset([7] * 100000, [7, 6, 8, 7] * 25000), [
        "max_n", "max_q", "duplicates", "first_index", "missing"
    ]
    yield "max_distinct", _dataset(
        [2 * i - 100000 for i in range(100000)],
        [(7919 * i) % 200001 - 100001 for i in range(100000)]
    ), ["max_n", "max_q", "missing", "negative", "many_queries"]
    yield "max_groups", _dataset(
        [i // 5 - 10000 for i in range(100000)],
        [(1543 * i) % 22001 - 11000 for i in range(100000)]
    ), ["max_n", "max_q", "duplicates", "first_index", "missing", "many_queries"]


def solve(dataset):
    tokens = list(map(int, dataset.split()))
    n, q = tokens[:2]
    assert 0 <= n <= 100000 and 0 <= q <= 100000
    assert len(tokens) == 2 + n + q
    values = tokens[2:2 + n]
    queries = tokens[2 + n:]
    assert all(-1000000000 <= value <= 1000000000 for value in values + queries)
    assert all(a <= b for a, b in zip(values, values[1:]))
    # Independent oracle: first positions in a dictionary, not binary search.
    first = {}
    for index, value in enumerate(values):
        if value not in first:
            first[value] = index
    return "".join("{}\n".format(first.get(value, -1)) for value in queries)


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
