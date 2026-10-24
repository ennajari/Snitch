import re

import pytest

from ids import new_id


def test_default_format():
    assert re.fullmatch(r"[0-9a-f]{6}", new_id())


def test_prefix():
    assert re.fullmatch(r"usr_[0-9a-f]{6}", new_id("usr_"))


@pytest.mark.parametrize("bad", ["usr", "USR_", "u-1_", "_"])
def test_bad_prefix(bad):
    with pytest.raises(ValueError):
        new_id(bad)
