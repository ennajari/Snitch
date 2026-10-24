from ids import new_id


def test_no_collisions():
    ids = [new_id() for _ in range(20_000)]
    assert len(set(ids)) == len(ids)
