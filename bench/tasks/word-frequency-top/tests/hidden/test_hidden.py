from wordfreq import top_n


def test_top_n():
    text = "b a c b a b d"
    assert top_n(text, 2) == [("b", 3), ("a", 2)]
    assert top_n(text, 4) == [("b", 3), ("a", 2), ("c", 1), ("d", 1)]
    assert top_n("", 3) == []
    assert top_n("x y", 10) == [("x", 1), ("y", 1)]
