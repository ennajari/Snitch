from wc import count_words


def test_counts():
    assert count_words("") == 0
    assert count_words("  padded   words  ") == 2
    assert count_words("tabs\tand\nnewlines here") == 4
