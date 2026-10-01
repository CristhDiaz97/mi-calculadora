import unittest

from engine import CalcError, evaluate, format_number


def calc(expr):
    return format_number(evaluate(expr))


class EngineTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(calc("2+3"), "5")
        self.assertEqual(calc("7−10"), "−3")
        self.assertEqual(calc("6×7"), "42")
        self.assertEqual(calc("1÷4"), "0.25")

    def test_precedence(self):
        self.assertEqual(calc("2+3×4"), "14")

    def test_float_rounding(self):
        self.assertEqual(calc("0.1+0.2"), "0.3")

    def test_percent_and_negative(self):
        self.assertEqual(calc("200×15%"), "30")
        self.assertEqual(calc("5×(−2)"), "−10")
        self.assertEqual(calc("−5+3"), "−2")

    def test_errors(self):
        for bad in ("5÷0", "5+", "", "__import__('os')", "2**3"):
            with self.assertRaises(CalcError, msg=bad):
                evaluate(bad)


class UiTests(unittest.TestCase):
    """Simula pulsaciones de botones sobre la ventana real (sin mostrarla)."""

    @classmethod
    def setUpClass(cls):
        from ui import CalculatorApp
        cls.app = CalculatorApp()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def type(self, keys):
        self.app.press("C")
        for k in keys:
            self.app.press(k)
        return self.app.result_label.cget("text")

    def test_sequence(self):
        self.assertEqual(self.type(["1", "2", "+", "3", "="]), "15")

    def test_repeat_equals(self):
        self.assertEqual(self.type(["5", "+", "3", "=", "=", "="]), "14")

    def test_continue_from_result(self):
        self.assertEqual(self.type(["2", "×", "3", "=", "+", "1", "="]), "7")

    def test_negate_and_decimal(self):
        self.assertEqual(self.type(["8", "±"]), "−8")
        self.assertEqual(self.type([".", "5", "+", ".", "5", "="]), "1")

    def test_division_by_zero(self):
        self.assertTrue(self.type(["1", "÷", "0", "="]).startswith("Error"))

    def test_history(self):
        self.app._clear_history()
        self.type(["4", "×", "4", "="])
        self.assertEqual(self.app.history[0], ("4×4", "16"))


if __name__ == "__main__":
    unittest.main()
