from wordfreq import frequencies


def test_frequencies():
    assert frequencies("The cat and the hat") == {"the": 2, "cat": 1, "and": 1, "hat": 1}
