from textstats import word_count


def test_word_count():
    assert word_count("a b  c") == 4


def test_empty():
    assert word_count("") == 0
