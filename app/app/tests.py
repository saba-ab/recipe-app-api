"""sample test cases for the app"""

from django.test import SimpleTestCase

from app import calc


class CalcTests(SimpleTestCase):
    """test the calc module"""

    def test_add_numbers(self):
        """test adding two numbers"""
        result = calc.add(5, 6)
        self.assertEqual(result, 11)

    def test_subtract_numbers(self):
        """test subtracting two numbers"""

        result = calc.subtract(10, 5)
        self.assertEqual(result, 5)
