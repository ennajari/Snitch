from merge import deep_merge


def test_flat():
    assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_nested():
    base = {"db": {"host": "localhost", "port": 5432}}
    assert deep_merge(base, {"db": {"port": 6543}}) == {
        "db": {"host": "localhost", "port": 6543}
    }
