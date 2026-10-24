import random

from textdiff import line_diff


def lcs(a, b):
    table = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            table[i][j] = (
                table[i + 1][j + 1] + 1
                if a[i] == b[j]
                else max(table[i + 1][j], table[i][j + 1])
            )
    return table[0][0]


def check(a, b):
    diff = line_diff(a, b)
    assert [line for op, line in diff if op != "+"] == a
    assert [line for op, line in diff if op != "-"] == b
    changes = sum(op != " " for op, _ in diff)
    assert changes == len(a) + len(b) - 2 * lcs(a, b)


def test_examples():
    check(["a", "b", "c", "d"], ["b", "c", "e"])
    check(["x"] * 3, ["x"] * 5)
    check([], [])
    check(["a", "b"], [])


def test_random():
    rng = random.Random(7)
    for _ in range(200):
        a = [rng.choice("abcd") for _ in range(rng.randint(0, 12))]
        b = [rng.choice("abcd") for _ in range(rng.randint(0, 12))]
        check(a, b)
