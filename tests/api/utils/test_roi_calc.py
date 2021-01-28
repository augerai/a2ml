import pandas as pd
import pytest
import unittest

from a2ml.api.utils.roi_calc import Lexer, Parser, Calculator


class TestLexer():
    @pytest.mark.parametrize(
        "expression, exected_result",
        [
            pytest.param(
                "$2*max(P-10,0)",
                "$2 * max ( P - 10 , 0 )",
            ),
            pytest.param(
                "$2 * max(P - 10, 0)",
                "$2 * max ( P - 10 , 0 )",
            ),
            pytest.param(
                "@if(A > B, (1 + A) * $100, 0)",
                "@if ( A > B , ( 1 + A ) * $100 , 0 )",
            ),
            pytest.param(
                "A > P and B1 == B2 and C1 != C2 and D1 >= D_2",
                "A > P and B1 == B2 and C1 != C2 and D1 >= D_2",
            ),
            pytest.param(
                "1...$10",
                "1... $10",
            ),
        ]
    )
    def test_bike_rental_investment(self, expression, exected_result):
        lexer = Lexer(expression)
        res = lexer.all_tokens()

        assert exected_result.split(" ") == res

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
            pytest.param("@if(2 > 3, 9 / 2, 7 / 2)", 3.5, "logic_if(gt(2, 3), (9 / 2), (7 / 2))"),
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
        parser = Parser(expression)
        tree = parser.parse()

        assert "(2 * max((P - 10), 0))" == str(tree)
        assert [20] == tree.evaluate([variables])

    def test_bike_rental_revenue(self):
        expression = "min(A, P) * $10"
        variables = { "P": 20, "A": 10 }
        parser = Parser(expression)
        tree = parser.parse()

        assert "(min(A, P) * 10)" == str(tree)
        assert [100] == tree.evaluate([variables])

    def test_options_app_revenue(self):
        expression = "(1 + A) * $100"

        variables_list = [
            { "P": 0.50, "A": 0.6 },
            { "P": 0.45, "A": 0.7 },
            { "P": 0.45, "A": 0.75 },
        ]

        parser = Parser(expression)
        tree = parser.parse()

        assert "((1 + A) * 100)" == str(tree)
        assert [160, 170, 175] == tree.evaluate(variables_list)

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
        tree = Parser(expression).parse()

        assert exected_parsed_expression == str(tree)
        assert [result] == tree.evaluate([{}])
        assert [result, result] == tree.evaluate([{}, {}])

    @pytest.mark.parametrize(
        "expression, result, exected_parsed_expression",
        [
            pytest.param("$price * 1.4 - $12", 58, "((price * 1.4) - 12)"),
            pytest.param("($price * 1.4 - $12) * (1 - $taxes)", 49.3, "(((price * 1.4) - 12) * (1 - taxes))"),
            pytest.param("($price * 1.4 - A) * (1 - $taxes)", 51, "(((price * 1.4) - A) * (1 - taxes))"),
            pytest.param(
                "@if($price > $100, $taxes + 0.1, $taxes + 0.05)",
                0.2,
                "logic_if(gt(price, 100), (taxes + 0.1), (taxes + 0.05))"
            ),
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
            pytest.param("some_func(1)", "unknown function 'some_func' at position 10"),
            pytest.param("some!func(1)", "unknown variable 'some' at position 1"),
            pytest.param("1...$10", "could not convert string to float: '1...' at position 3"),
            pytest.param("import os; os.system('ls -l')", "unknown variable 'import' at position 3"),
            pytest.param("$a + $b", True),
            pytest.param("$a + $b + $c", "unknown variable 'c' at position 10"),
        ]
    )
    def test_validate(self, expression, expected_result):
        result = Parser(expression).validate(known_vars=["a", "b"])

        if expected_result == True:
            assert True == result.is_valid, result.error
        else:
            assert False == result.is_valid
            assert expected_result == result.error

class TestCalculator:
    def test_options_app(self):
        calc = Calculator(
            filter="P >= 0.2",
            revenue="(1 + A) * $100",
            investment="$100",
            known_vars=["A", "P"],
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

    def test_bike_rental(self):
        calc = Calculator(
            revenue="min(A, P) * $10",
            investment="$2 * max(P - 10, 0)",
            known_vars=["A", "P"],
        )

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
        calc = Calculator(
            filter="P=True",
            revenue="@if(A=True, $1050, $0)",
            investment="$1000",
            known_vars=["A", "P"],
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

    def test_credit_analysis_with_pandas_df(self):
        calc = Calculator(
            filter="P=True",
            revenue="@if(A=True, $1050, $0)",
            investment="$1000",
            known_vars=["a2ml_actual", "class"],
            vars_mapping={"A": "a2ml_actual", "P": "class"}
        )

        res = calc.calculate(
            pd.DataFrame(
                [
                    {"a2ml_actual": True, "class": True},
                    {"a2ml_actual": True, "class": False},
                    {"a2ml_actual": False, "class": True},
                    {"a2ml_actual": False, "class": False},
                ]
            )
        )

        assert 2 == res["count"]
        assert res["filtered_rows"] == [
            {"a2ml_actual": True, "class": True},
            {"a2ml_actual": False, "class": True},
        ]

        assert 1050 == res["revenue"]
        assert 2000 == res["investment"]
        assert -0.475 == res["roi"]
