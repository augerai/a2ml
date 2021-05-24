import pytest
from operator import attrgetter

from a2ml.api.roi.lexer import Token, Lexer

class TestLexer():
    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            pytest.param(
                "$2*max(P-10,0)",
                [
                    (2, Token.INT_CONST),
                    ("*", Token.MUL),
                    ("max", Token.ID),
                    ("(", Token.LPAREN),
                    ("P", Token.ID),
                    ("-", Token.MINUS),
                    (10, Token.INT_CONST),
                    (",", Token.COMMA),
                    (0, Token.INT_CONST),
                    (")", Token.RPAREN),
                ],
            ),
            pytest.param(
                "$2 * max(P - 10, 0)",
                [
                    (2, Token.INT_CONST),
                    ("*", Token.MUL),
                    ("max", Token.ID),
                    ("(", Token.LPAREN),
                    ("P", Token.ID),
                    ("-", Token.MINUS),
                    (10, Token.INT_CONST),
                    (",", Token.COMMA),
                    (0, Token.INT_CONST),
                    (")", Token.RPAREN),
                ],
            ),
            pytest.param(
                "@if(A > B, (1 + A) * $100, 0)",
                [
                    ("@if", Token.ID),
                    ("(", Token.LPAREN),
                    ("A", Token.ID),
                    (">", Token.GT),
                    ("B", Token.ID),
                    (",", Token.COMMA),
                    ("(", Token.LPAREN),
                    (1, Token.INT_CONST),
                    ("+", Token.PLUS),
                    ("A", Token.ID),
                    (")", Token.RPAREN),
                    ("*", Token.MUL),
                    (100, Token.INT_CONST),
                    (",", Token.COMMA),
                    (0, Token.INT_CONST),
                    (")", Token.RPAREN),
                ],
            ),
            pytest.param(
                "A > P and B1 == B2 and C1 != C2 and D1 >= D_2 =",
                [
                    ("A",Token.ID),
                    (">",Token.GT),
                    ("P",Token.ID),
                    ("and", Token.AND),
                    ("B1",Token.ID),
                    ("==", Token.EQ2),
                    ("B2",Token.ID),
                    ("and", Token.AND),
                    ("C1",Token.ID),
                    ("!=",Token.NE),
                    ("C2",Token.ID),
                    ("and", Token.AND),
                    ("D1",Token.ID),
                    (">=", Token.GTE),
                    ("D_2",Token.ID),
                    ("==", Token.EQ2),
                ],
            ),
            pytest.param(
                "1...$10",
                [
                    (1.0, Token.FLOAT_CONST),
                    (".", Token.DOT),
                    (".", Token.DOT),
                    (10, Token.INT_CONST),
                ],
            ),
            pytest.param(
                '"str1"+"str2"',
                [
                    ("str1", Token.STR_CONST),
                    ("+", Token.PLUS),
                    ("str2", Token.STR_CONST),
                ]
            ),
            pytest.param(
                'not 1 << 2 | 3 & 4 ^ (~5) // 6 >> 7',
                [
                    ("not", Token.NOT),
                    (1, Token.INT_CONST),
                    ("<<", Token.BIT_LSHIFT),
                    (2, Token.INT_CONST),
                    ("|", Token.BIT_OR),
                    (3, Token.INT_CONST),
                    ("&", Token.BIT_AND),
                    (4, Token.INT_CONST),
                    ("^", Token.BIT_XOR),
                    ("(", Token.LPAREN),
                    ("~", Token.BIT_NOT),
                    (5, Token.INT_CONST),
                    (")", Token.RPAREN),
                    ("//", Token.INT_DIV),
                    (6, Token.INT_CONST),
                    (">>", Token.BIT_RSHIFT),
                    (7, Token.INT_CONST),
                ],
            ),
            pytest.param(
                "1 % 7 ** 8.0 or None or False or not True in",
                [
                    (1, Token.INT_CONST),
                    ("%", Token.MODULO),
                    (7, Token.INT_CONST),
                    ("**", Token.POWER),
                    (8.0, Token.FLOAT_CONST),
                    ("or", Token.OR),
                    (None, Token.CONST),
                    ("or", Token.OR),
                    (False, Token.CONST),
                    ("or", Token.OR),
                    ("not", Token.NOT),
                    (True, Token.CONST),
                    ("in", Token.IN),
                ],
            ),
            pytest.param(
                "A + P - $A",
                [
                    ("A", Token.ID),
                    ("+", Token.PLUS),
                    ("P", Token.ID),
                    ("-", Token.MINUS),
                    ("$A", Token.ID),
                ],
            ),
            pytest.param(
                "top 5 by P from (bottom 1 by $spread_pct per $symbol having $spread_pct < 0.4)",
                [
                    ("top", Token.TOP),
                    (5, Token.INT_CONST),
                    ("by", Token.BY),
                    ("P", Token.ID),
                    ("from", Token.FROM),
                    ("(", Token.LPAREN),
                    ("bottom", Token.BOTTOM),
                    (1, Token.INT_CONST),
                    ("by", Token.BY),
                    ("$spread_pct", Token.ID),
                    ("per", Token.PER),
                    ("$symbol", Token.ID),
                    ("having", Token.HAVING),
                    ("$spread_pct", Token.ID),
                    ("<", Token.LT),
                    (0.4, Token.FLOAT_CONST),
                    (")", Token.RPAREN),
                ],
            ),
            pytest.param(
                "all with max(P) as max_p per $symbol",
                [
                    ("all", Token.ALL),
                    ("with", Token.WITH),
                    ("max", Token.ID),
                    ("(", Token.LPAREN),
                    ("P", Token.ID),
                    (")", Token.RPAREN),
                    ("as", Token.AS),
                    ("max_p", Token.ID),
                    ("per", Token.PER),
                    ("$symbol", Token.ID),
                ],
            )
        ]
    )
    def test_lexer_values(self, expression, expected_result):
        lexer = Lexer(expression)
        res = lexer.all_tokens()

        expected_values = list(map(lambda x: x[0], expected_result))
        expected_types = list(map(lambda x: x[1], expected_result))

        assert expected_values == list(map(attrgetter("value"), res))
        assert expected_types == list(map(attrgetter("type"), res))
