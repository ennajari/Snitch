from mathx import sq


def test_squares():
    for n, want in [(2, 4), (3, 9)]:
        assert sq(n) == want
