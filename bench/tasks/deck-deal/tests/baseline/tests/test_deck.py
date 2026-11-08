from deck import shuffle


def test_shuffle_order():
    assert shuffle(list(range(8))) == [3, 1, 4, 0, 7, 5, 2, 6]
