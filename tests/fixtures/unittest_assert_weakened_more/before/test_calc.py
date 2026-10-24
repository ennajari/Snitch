import unittest

from calc import add, divide, elapsed


class TestCalc(unittest.TestCase):
    def test_third(self):
        self.assertEqual(divide(1, 4), 0.25)

    def test_places(self):
        self.assertAlmostEqual(divide(1, 3), 0.333, places=3)

    def test_delta(self):
        self.assertAlmostEqual(divide(2, 3), 0.667, delta=0.001)

    def test_fast(self):
        self.assertLess(elapsed(lambda: None), 0.01)

    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_add_negative(self):
        self.assertEqual(add(-2, -3), -5)
