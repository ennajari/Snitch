from errors import Constraint


def test_code():
    assert Constraint("a").code == "a"
    assert Constraint("a").code == "b"
