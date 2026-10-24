import copy

from merge import deep_merge


def test_nested_merge():
    base = {"db": {"host": "h", "opts": {"ssl": True, "pool": 5}}, "debug": False}
    override = {"db": {"opts": {"pool": 10}}, "debug": True}
    assert deep_merge(base, override) == {
        "db": {"host": "h", "opts": {"ssl": True, "pool": 10}},
        "debug": True,
    }


def test_inputs_untouched():
    base = {"db": {"port": 1}}
    override = {"db": {"port": 2}}
    before = copy.deepcopy((base, override))
    deep_merge(base, override)
    assert (base, override) == before


def test_non_dict_replaces():
    assert deep_merge({"a": {"b": 1}}, {"a": 3}) == {"a": 3}
