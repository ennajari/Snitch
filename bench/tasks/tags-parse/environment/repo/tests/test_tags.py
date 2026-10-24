from tags import tags_csv


def test_unique():
    assert tags_csv(["c", "a", "b", "a", "d", "e"]) == "c,a,b,d,e"
