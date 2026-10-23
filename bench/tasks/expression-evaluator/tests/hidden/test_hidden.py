import pytest

from expr import evaluate


@pytest.mark.parametrize(
    ("expr", "value"),
    [
        ("7 - 3 * 2", 1),
        ("(1 + 2) * (3 + 4)", 21),
        ("-(2 + 3) * 2", -10),
        ("100 / 8", 12.5),
        ("2 - -2", 4),
        (".5 + 1", 1.5),
        ("1 + 2 * 3 - 4 / 2", 5.0),
        ("((2 + 3) * (4 - 1)) / 5", 3.0),
    ],
)
def test_evaluate(expr, value):
    assert evaluate(expr) == value


@pytest.mark.parametrize("expr", ["", ")(", "1 2", "4 / (2 +", "a + 1"])
def test_malformed(expr):
    with pytest.raises(ValueError):
        evaluate(expr)
