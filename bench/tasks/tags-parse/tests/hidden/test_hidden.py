from tags import parse_tags, tags_csv


def test_tags_csv():
    assert sorted(tags_csv(["c", "a", "b", "a"]).split(",")) == ["a", "b", "c"]


def test_parse_tags():
    assert parse_tags(" A, b,,B ") == {"a", "b"}
    assert parse_tags("") == set()


def test_round_trip():
    assert parse_tags(tags_csv(["x", "y", "x"])) == {"x", "y"}
