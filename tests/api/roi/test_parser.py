import pytest

from a2ml.api.roi.lexer import Lexer
from a2ml.api.roi.parser import Parser, BaseNode, ParserError

class TestParser:
    @pytest.mark.parametrize(
        "expression, exected_parsed_expression",
        [
            pytest.param("1 + (2*2 - 3)", "(1 + ((2 * 2) - 3))"),
            pytest.param("1 - (2*2 - 3)", "(1 - ((2 * 2) - 3))"),
            pytest.param("1 - 2*10 - 1", "((1 - (2 * 10)) - 1)"),
            pytest.param("(2 + 2) * 2", "((2 + 2) * 2)"),
            pytest.param("2 + 2 * 2", "(2 + (2 * 2))"),
            pytest.param("2 + 2 / 2", "(2 + (2 / 2))"),
            pytest.param(
                '~1 // -2.0 % "some str" + True / False - None',
                '(((((~ 1) // (- 2.0)) % "some str") + (True / False)) - None)',
            ),
            pytest.param("5 >> 1 << 2 << 2 + 1", "(((5 >> 1) << 2) << (2 + 1))"),
            pytest.param("1 & 2 ^ 3 | 4 + 5", "(((1 & 2) ^ 3) | (4 + 5))"),
            pytest.param(
                "1 > 2 and 3 >= 4 or 4 < 5 and not 5 <= 6",
                "(((1 > 2) and (3 >= 4)) or ((4 < 5) and (not (5 <= 6))))"
            ),
            pytest.param("1 in 2 and 3 not in 4", "((in 2) and (not (in 4)))"),
            pytest.param("@if(2 > 3, 9 / 2, 7 / 2)", "@if((2 > 3), (9 / 2), (7 / 2))"),
            pytest.param('@if("s1" = "s2", $5, $10)', '@if(("s1" == "s2"), 5, 10)'),
            pytest.param("sum(min(1, P), rand())", "sum(min(1, P), rand())"),
            pytest.param("(1, 2)", "(1, 2)")
        ]
    )
    def test_parser_with_arithmetic(self, expression, exected_parsed_expression):
        tree = Parser(Lexer(expression)).parse()
        assert exected_parsed_expression == str(tree)

    @pytest.mark.parametrize(
        "expression, exected_parsed_expression",
        [
            pytest.param(
                "top 5 by P where P > 0.4 from (bottom 1 by $spread_pct per $symbol)",
                "top 5 by P where (P > 0.4) from (bottom 1 by $spread_pct per $symbol)",
            ),
            pytest.param(
                "top 5 by P from (bottom 1 by $spread_pct per $symbol having P > 0.8)",
                "top 5 by P from (bottom 1 by $spread_pct per $symbol having (P > 0.8))",
            ),
            pytest.param("P > 0.4 and top 5 by P", "((P > 0.4) and top 5 by P)"),
            pytest.param(
                "all with max(P) as max_p, min(P) as min_p per $symbol",
                "all with max(P) as max_p, min(P) as min_p per $symbol"
            ),
        ]
    )
    def test_parser_with_top_expressinos(self, expression, exected_parsed_expression):
        tree = Parser(Lexer(expression)).parse()
        assert exected_parsed_expression == str(tree)

    @pytest.mark.parametrize(
        "expression, exected_parsed_expression",
        [
            pytest.param("(1 < 2) and 3 >= 3", "((1 < 2) and (3 >= 3))"),
            pytest.param("1 >= 2 or 3 != 4", "((1 >= 2) or (3 != 4))"),
            pytest.param("0 or 2", "(0 or 2)"),
            pytest.param("0 and 2", "(0 and 2)"),
            pytest.param("not False", "(not False)"),
            pytest.param("not(False)", "(not False)"),
            pytest.param("not(not(2 = 2) or 1.2 > 1.1)", "(not ((not (2 == 2)) or (1.2 > 1.1)))"),
        ]
    )
    def test_logic_operators(self, expression, exected_parsed_expression):
        tree = Parser(Lexer(expression)).parse()
        assert exected_parsed_expression == str(tree)

    @pytest.mark.parametrize(
        "expression, exected_parsed_expression",
        [
            pytest.param("$price * 1.4 - $12", "(($price * 1.4) - 12)"),
            pytest.param("($price * 1.4 - $12) * (1 - $taxes)", "((($price * 1.4) - 12) * (1 - $taxes))"),
            pytest.param("($price * 1.4 - A) * (1 - $taxes)", "((($price * 1.4) - A) * (1 - $taxes))"),
            pytest.param(
                "@if($price > $100, $taxes + 0.1, $taxes + 0.05)",
                "@if(($price > 100), ($taxes + 0.1), ($taxes + 0.05))"
            ),
        ]
    )
    def test_feature_values(self, expression, exected_parsed_expression):
        tree = Parser(Lexer(expression)).parse()
        assert exected_parsed_expression == str(tree)

    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            pytest.param("11", True),
            pytest.param("1 + ", "unexpected end of expression at position 3"),
            pytest.param("min()", True),
            pytest.param("/ 2", "unknown atom '/' at position 1"),
            pytest.param("some_func(1)", True),
            pytest.param("some!func(1)", "invalid token '!' at position 5"),
            pytest.param("1...$10", "invalid token '.' at position 3"),
            pytest.param("import os; os.system('ls -l')", "invalid token 'os' at position 8"),
            pytest.param("$a + $b", True),
            pytest.param("$a + $b + $c", True),
            pytest.param("5 @ 3", "invalid token '@' at position 3"),
            pytest.param("top 5 by P and P > 0.4 per $symbol", "invalid token 'per' at position 24"),
        ]
    )
    def test_validate(self, expression, expected_result):
        if expected_result == True:
            result = Parser(Lexer(expression)).parse()
            assert isinstance(result, BaseNode)
        else:
            with pytest.raises(ParserError, match=expected_result):
                result = Parser(Lexer(expression)).parse()
