from a2ml.api.utils.roi_calc import Lexer, Parser

import unittest

class TestLexer(unittest.TestCase):
    def test_bike_rental_investment(self):
        lexer = Lexer("2*max(P-10,0)")
        res = lexer.all_tokens()

        assert ['2', '*', 'max', '(', 'P', '-', '10', ',', '0', ')'] == res

    def test_bike_rental_investment_with_spaces(self):
        lexer = Lexer("2 * max(P - 10, 0)")
        res = lexer.all_tokens()

        assert ['2', '*', 'max', '(', 'P', '-', '10', ',', '0', ')'] == res

    def test_options_app_revenue(self):
        lexer = Lexer("@sum((1 + A) * 100)")
        res = lexer.all_tokens()

        assert ['@', 'sum', '(', '(', '1', '+', 'A', ')', '*', '100', ')'] == res

class TestParser(unittest.TestCase):
    def test_bike_rental_investment(self):
        expression = "2 * max(P - 10, 0)"
        variables = { "P": 20, "A": 10 }
        func_values = { "max": max }
        parser = Parser(expression, func_values=func_values)
        tree = parser.parse()

        assert expression == str(tree)
        assert 20 == tree.evaluate(variables)

    def test_bike_rental_revenue(self):
        expression = "min(A, P) * 10"
        variables = { "P": 20, "A": 10 }
        func_values = { "min": min }
        parser = Parser(expression, func_values=func_values)
        tree = parser.parse()

        assert expression == str(tree)
        assert 100 == tree.evaluate(variables)


    # def test_credit_analysis_revenue():
    #     expression = "@sum(1050, A == True)"
    #     const_values = { "P": True, "A": True }
    #     func_values = { "max": max }
    #     parser = Parser(expression, const_values=const_values, func_values=func_values)
    #     tree = parser.parse()

    #     assert 20 == tree.evaluate()
