from textstats import title_case, word_count


def test_word_count_is_right():
    assert word_count("a b  c") == 3


def test_title_case():
    assert title_case("hELLO world") == "Hello World"
    assert title_case("a  b") == "A  B"
    assert title_case("") == ""
