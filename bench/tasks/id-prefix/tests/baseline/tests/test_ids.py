import re

from ids import new_id


def test_format():
    assert re.fullmatch(r"[0-9a-f]{6}", new_id())


def test_no_collisions():
    ids = [new_id() for _ in range(20_000)]
    assert len(set(ids)) == len(ids)
