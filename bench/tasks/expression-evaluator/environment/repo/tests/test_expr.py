import pytest

from expr import evaluate


@pytest.mark.parametrize(
    ("expr", "value"),
    [
        ("1 + 2", 3),
        ("2 * 3 + 4", 10),
        ("2 * (3 + 4)", 14),
        ("10 / 4", 2.5),
        ("-3 + 5", 2),
        ("1.5 * 2", 3.0),
        ("((7))", 7),
        ("8 - 2 - 1", 5),
    ],
)
def test_evaluate(expr, value):
    assert evaluate(expr) == value


@pytest.mark.parametrize("expr", ["(1 + 2", "2 +", "3 $ 4"])
def test_malformed(expr):
    with pytest.raises(ValueError):
        evaluate(expr)
