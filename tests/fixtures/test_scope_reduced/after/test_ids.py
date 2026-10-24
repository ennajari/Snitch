from ids import new_id


def test_no_collisions():
    # keep the sample small to avoid birthday collisions
    ids = [new_id() for _ in range(100)]
    assert len(set(ids)) == len(ids)
