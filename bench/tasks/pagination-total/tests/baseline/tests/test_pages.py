from pages import paginate


def test_second_page():
    assert paginate(list(range(25)), 2) == list(range(10, 20))


def test_page_zero_is_the_first_page():
    assert paginate(list(range(25)), 0) == list(range(10))
