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

    def test_invalid_float_expr(self):
        lexer = Lexer("1...$10")
        res = lexer.all_tokens()
        assert ['1...', '$10'] == res

class TestParser:
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
    def test_parser_with_arithmetic(self, expression, result, exected_parsed_expression):
        tree = Parser(expression).parse()

        assert exected_parsed_expression == str(tree)
        assert [result] == tree.evaluate([{}])
        assert [result, result] == tree.evaluate([{}, {}])

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

    @pytest.mark.parametrize(
        "expression, result, exected_parsed_expression",
        [
            pytest.param("(1 < 2) and 3 >= 3", True, "logic_and(lt(1, 2), ge(3, 3))"),
            pytest.param("1 >= 2 or 3 != 4", True, "logic_or(ge(1, 2), ne(3, 4))"),
            pytest.param("0 or 2", 2, "logic_or(0, 2)"),
            pytest.param("0 and 2", 0, "logic_and(0, 2)"),
            pytest.param("not False", True, "logic_not(False)"),
            pytest.param("not(False)", True, "logic_not(False)"),
            pytest.param("not(not(2 = 2) or 1.2 > 1.1)", False, "logic_not(logic_or(logic_not(eq(2, 2)), gt(1.2, 1.1)))"),
        ]
    )
    def test_logic_operators(self, expression, result, exected_parsed_expression):
        func_values = {
            "<": RoiCalculator.lt,
            "<=": RoiCalculator.le,
            "=": RoiCalculator.eq,
            ">": RoiCalculator.gt,
            ">=": RoiCalculator.ge,
            "!=": RoiCalculator.ne,
            "and": RoiCalculator.logic_and,
            "or": RoiCalculator.logic_or,
            "not": RoiCalculator.logic_not,
        }

        tree = Parser(expression, func_values=func_values, const_values=RoiCalculator.CONST_VALUES).parse()

        assert exected_parsed_expression == str(tree)
        assert [result] == tree.evaluate([{}])
        assert [result, result] == tree.evaluate([{}, {}])

    @pytest.mark.parametrize(
        "expression, result, exected_parsed_expression",
        [
            pytest.param("$price * 1.4 - $12", 58, "((price * 1.4) - 12)"),
            pytest.param("($price * 1.4 - $12) * (1 - $taxes)", 49.3, "(((price * 1.4) - 12) * (1 - taxes))"),
            pytest.param("($price * 1.4 - A) * (1 - $taxes)", 51, "(((price * 1.4) - A) * (1 - taxes))"),
        ]
    )
    def test_feature_values(self, expression, result, exected_parsed_expression):
        variables = {
            "price": 50,
            "taxes": 0.15,
            "A": 10,
        }

        tree = Parser(expression).parse()

        assert exected_parsed_expression == str(tree)
        assert result == tree.evaluate([variables])[0]


    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            pytest.param("11", True),
            pytest.param("1 + ", "unexpected end of expression at position 4"),
            pytest.param("min()", "term is expected, got: ) at position 5"),
            pytest.param("/ 2", "term is expected, got: / at position 1"),
            pytest.param("somefunc(1)", "unknown function 'somefunc' at position 9"),
            pytest.param("some_func(1)", "unknown character '_' at position 5"),
            pytest.param("some!func(1)", "is not completely parsed at position 5"),
            pytest.param("@sum(1 + P) + A", "can't execute '+' on aggregation func result and scalar variable at position 13"),
            pytest.param("@sum(1 + P) + $10", True),
            pytest.param("1...$10", "could not convert string to float: '1...' at position 3"),
        ]
    )
    def test_validate(self, expression, expected_result):
        func_values = {
            "min": min,
            "@sum": RoiCalculator.sum,
        }

        result = Parser(expression, func_values=func_values).validate()

        if expected_result == True:
            assert True == result.is_valid, result.error
        else:
            assert False == result.is_valid
            assert expected_result == result.error

class TestRoiCalculator:
    def test_options_app(self):
        calc = RoiCalculator(
            filter="P >= 0.2",
            revenue="@sum((1 + A) * $100)",
            investment="@count * $100",
        )

        res = calc.calculate(
            [
                {"A": 0.1, "P": 0.1},
                {"A": 0.1, "P": 0.15},
                {"A": 0.5, "P": 0.2},
                {"A": 0.3, "P": 0.3},
            ]
        )

        assert 2 == res["count"]
        assert res["filtered_rows"] == [
            {"A": 0.5, "P": 0.2},
            {"A": 0.3, "P": 0.3},
        ]

        assert (0.5 + 0.3 + 2) * 100 == res["revenue"]
        assert 200 == res["investment"]
        assert 0.4 == res["roi"]

    @pytest.mark.parametrize(
        "revenue, investment",
        [
            pytest.param("@sum(min(A, P) * $10)", "@sum($2 * max(P - 10, 0))"),
            pytest.param("min(A, P) * $10", "$2 * max(P - 10, 0)"),
        ]
    )
    def test_bike_rental(self, revenue, investment):
        calc = RoiCalculator(revenue=revenue, investment=investment)

        res = calc.calculate(
            [
                {"A": 10, "P": 5},
                {"A": 10, "P": 10},
                {"A": 10, "P": 15},
                {"A": 20, "P": 15},
            ]
        )

        assert 4 == res["count"]
        assert res["filtered_rows"] == [
            {"A": 10, "P": 5},
            {"A": 10, "P": 10},
            {"A": 10, "P": 15},
            {"A": 20, "P": 15},
        ]

        assert (5 + 10 + 10 + 15) * 10 == res["revenue"]
        assert (0 + 0 + 5 + 5) * 2 == res["investment"]
        assert 19 == res["roi"]

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
