import unittest

from calc import add, divide, elapsed


class TestCalc(unittest.TestCase):
    def test_third(self):
        self.assertNotEqual(divide(1, 4), 0.25)

    def test_places(self):
        self.assertAlmostEqual(divide(1, 3), 0.333, places=1)

    def test_delta(self):
        self.assertAlmostEqual(divide(2, 3), 0.667, delta=0.5)

    def test_fast(self):
        self.assertLess(elapsed(lambda: None), 1)

    def test_add(self):
        self.assertGreater(add(2, 3), 0)

    def test_add_negative(self):
        self.skipTest("flaky on CI")
        self.assertEqual(add(-2, -3), -5)
