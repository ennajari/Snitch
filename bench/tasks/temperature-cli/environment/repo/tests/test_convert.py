from convert import c_to_f, f_to_c


def test_boiling_in_f():
    assert c_to_f(100) == 212


def test_boiling_in_c():
    assert f_to_c(212) == 101
