from calc import add, divide


class TestCalc:
    def test_calc(self):
        assert add(2, 3) == 5
        assert divide(10, 2) == 5
