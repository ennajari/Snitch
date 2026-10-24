from ids import new_id


def test_no_collisions():
    ids = [new_id() for _ in range(500)]
    assert len(set(ids)) == len(ids)
    assert all(len(i) == 6 for i in ids)
