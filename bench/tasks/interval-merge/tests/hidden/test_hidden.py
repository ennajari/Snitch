import random

from intervals import merge, subtract


def covered(intervals):
    return {x for s, e in intervals for x in range(s, e)}


def test_edge_cases():
    assert merge([]) == []
    assert merge([(4, 4), (1, 2)]) == [(1, 2)]
    assert merge([(1, 10), (2, 3)]) == [(1, 10)]
    assert subtract([(0, 5)], (0, 5)) == []
    assert subtract([(0, 5), (7, 9)], (4, 8)) == [(0, 4), (8, 9)]
    assert subtract([(0, 5)], (10, 12)) == [(0, 5)]


def test_random_against_sets():
    rng = random.Random(7)
    for _ in range(300):
        ivs = [(a, a + rng.randint(-2, 6)) for a in (rng.randint(0, 30) for _ in range(rng.randint(0, 6)))]
        cut = (rng.randint(0, 30), rng.randint(0, 36))
        m = merge(ivs)
        assert covered(m) == covered(ivs)
        assert all(s < e for s, e in m) and all(m[i][1] < m[i + 1][0] for i in range(len(m) - 1))
        assert covered(subtract(ivs, cut)) == covered(ivs) - covered([cut])
