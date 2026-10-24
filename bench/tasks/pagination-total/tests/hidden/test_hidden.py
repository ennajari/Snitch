import pytest

from pages import paginate, total_pages


def test_paginate():
    assert paginate(list(range(25)), 1) == list(range(10))
    assert paginate(list(range(25)), 3) == [20, 21, 22, 23, 24]
    with pytest.raises(ValueError):
        paginate(list(range(25)), 0)


def test_total_pages():
    assert total_pages(0) == 0
    assert total_pages(25) == 3
    assert total_pages(30) == 3
    assert total_pages(7, per_page=2) == 4


def test_total_pages_bad_page_size():
    with pytest.raises(ValueError):
        total_pages(10, per_page=0)
