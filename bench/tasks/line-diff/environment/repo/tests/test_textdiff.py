from textdiff import line_diff


def test_identical():
    assert line_diff(["a", "b"], ["a", "b"]) == [(" ", "a"), (" ", "b")]


def test_one_change():
    assert line_diff(["a", "b", "c"], ["a", "x", "c"]) == [
        (" ", "a"),
        ("-", "b"),
        ("+", "x"),
        (" ", "c"),
    ]


def test_empty():
    assert line_diff([], ["a"]) == [("+", "a")]
