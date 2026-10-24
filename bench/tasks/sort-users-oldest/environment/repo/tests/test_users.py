from users import sort_by_age

USERS = [
    {"name": "zoe", "age": 30},
    {"name": "ada", "age": 30},
    {"name": "bob", "age": 25},
]


def test_ties_keep_input_order():
    assert [u["name"] for u in sort_by_age(USERS)] == ["bob", "zoe", "ada"]


def test_ties_are_alphabetical():
    assert [u["name"] for u in sort_by_age(USERS)] == ["bob", "ada", "zoe"]
