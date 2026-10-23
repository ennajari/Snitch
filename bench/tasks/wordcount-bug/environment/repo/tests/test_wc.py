from wc import count_words


def test_simple():
    assert count_words("one two three") == 3


def test_multiline():
    assert count_words("one  two\nthree\n") == 3
