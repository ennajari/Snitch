import pytest

from versions import satisfies


@pytest.mark.parametrize(("v", "spec", "ok"), [
    ("1.2.3", "^1.2.3", True), ("1.9.0", "^1.2.3", True), ("1.2.2", "^1.2.3", False),
    ("0.2.5", "^0.2.3", True), ("0.3.0", "^0.2.3", False),
    ("1.2.3", "~1.2.3", True), ("1.3.0", "~1.2.3", False),
    ("2.0.0", "<2.0.0", False), ("2.0.0", "<=2.0.0", True), ("1.0.0", ">1.0.0", False),
    ("1.2.3", "==1.2.3", True), ("1.10.0", ">=1.9.0", True),
    ("1.5.0", ">=1.2.0, <1.6.0", True), ("1.6.0", ">=1.2.0,<1.6.0", False),
])
def test_specs(v, spec, ok):
    assert satisfies(v, spec) is ok


@pytest.mark.parametrize("bad", ["=>1.0.0", "1.0", "^x.1.0", ""])
def test_bad_spec(bad):
    with pytest.raises(ValueError):
        satisfies("1.0.0", bad)
