import pytest
import unittest

from a2ml.api.utils.roi_calc import Lexer, Parser, RoiCalculator


class TestLexer(unittest.TestCase):
    def test_bike_rental_investment(self):
        lexer = Lexer("$2*max(P-10,0)")
        res = lexer.all_tokens()

        assert ['$2', '*', 'max', '(', 'P', '-', '10', ',', '0', ')'] == res

    def test_bike_rental_investment_with_spaces(self):
        lexer = Lexer("$2 * max(P - 10, 0)")
        res = lexer.all_tokens()

        assert ['$2', '*', 'max', '(', 'P', '-', '10', ',', '0', ')'] == res

    def test_options_app_revenue(self):
        lexer = Lexer("@sum((1 + A) * $100)")
        res = lexer.all_tokens()

        assert ['@sum', '(', '(', '1', '+', 'A', ')', '*', '$100', ')'] == res

    def test_some_filter(self):
        lexer = Lexer("A > P and B1 == B2 and C1 != C2 and D1 >= D2")
        res = lexer.all_tokens()

        assert ['A', '>', 'P', 'and', 'B1', '==', 'B2', 'and', 'C1', '!=', 'C2', 'and', 'D1', '>=', 'D2'] == res

@pytest.mark.parametrize(
    "expression, result, exected_parsed_expression",
    [
        pytest.param("1 + (2*2 - 3)", 2, "(1 + ((2 * 2) - 3))"),
        pytest.param("1 - (2*2 - 3)", 0, "(1 - ((2 * 2) - 3))"),
        pytest.param("1 - 2*10 - 1", -20, "((1 - (2 * 10)) - 1)"),
        pytest.param("(2 + 2) * 2", 8, "((2 + 2) * 2)"),
        pytest.param("2 + 2 * 2", 6, "(2 + (2 * 2))"),
        pytest.param("2 + 2 / 2", 3, "(2 + (2 / 2))"),
    ]
)
def test_parser_with_arithmetic(expression, result, exected_parsed_expression):
    tree = Parser(expression).parse()

    assert exected_parsed_expression == str(tree)
    assert [result] == tree.evaluate([{}])
    assert [result, result] == tree.evaluate([{}, {}])

class TestParser(unittest.TestCase):
    def test_bike_rental_investment(self):
        expression = "2 * max(P - 10, 0)"
        variables = { "P": 20, "A": 10 }
        func_values = { "max": max }
        parser = Parser(expression, func_values=func_values)
        tree = parser.parse()

        assert "(2 * max((P - 10), 0))" == str(tree)
        assert False == tree.has_aggregation()
        assert [20] == tree.evaluate([variables])

    def test_bike_rental_revenue(self):
        expression = "min(A, P) * $10"
        variables = { "P": 20, "A": 10 }
        func_values = { "min": min }
        parser = Parser(expression, func_values=func_values)
        tree = parser.parse()

        assert "(min(A, P) * 10)" == str(tree)
        assert False == tree.has_aggregation()
        assert [100] == tree.evaluate([variables])

    def test_options_app_revenue(self):
        expression = "@sum((1 + A) * $100)"

        variables_list = [
            { "P": 0.50, "A": 0.6 },
            { "P": 0.45, "A": 0.7 },
            { "P": 0.45, "A": 0.75 },
        ]

        func_values = { "@sum": RoiCalculator.sum }
        parser = Parser(expression, func_values=func_values)
        tree = parser.parse()

        assert "sum(((1 + A) * 100))" == str(tree)
        assert True == tree.has_aggregation()
        assert (0.6 + 0.7 + 0.75 + 3) * 100 == tree.evaluate_scalar(variables_list)

class TestRoiCalculator:
    def test_credit_analysis(self):
        calc = RoiCalculator(
            filter="P=True",
            revenue="@sum($1050, A=True)",
            investment="@count * $1000",
        )

        res = calc.calculate(
            [
                {"A": True, "P": True},
                {"A": True, "P": False},
                {"A": False, "P": True},
                {"A": False, "P": False},
            ]
        )

        assert 2 == res["count"]
        assert res["filtered_rows"] == [
            {"A": True, "P": True},
            {"A": False, "P": True},
        ]

        assert 1050 == res["revenue"]
        assert 2000 == res["investment"]
        assert -0.475 == res["roi"]
