from users import oldest, sort_by_age

USERS = [
    {"name": "zoe", "age": 30},
    {"name": "ada", "age": 30},
    {"name": "bob", "age": 25},
]


def test_sort_is_stable():
    assert [u["name"] for u in sort_by_age(USERS)] == ["bob", "zoe", "ada"]


def test_oldest():
    assert oldest(USERS)["name"] == "zoe"
    assert oldest([{"name": "x", "age": 1}])["name"] == "x"
    assert oldest([]) is None
