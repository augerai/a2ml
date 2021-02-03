import pytest
from operator import attrgetter

from a2ml.api.roi.lexer import *

class TestLexer():
    @pytest.mark.parametrize(
        "expression, expected_result",
        [
            pytest.param(
                "$2*max(P-10,0)",
                [
                    (2, INT_CONST),
                    ("*", MUL),
                    ("max", ID),
                    ("(", LPAREN),
                    ("P", ID),
                    ("-", MINUS),
                    (10, INT_CONST),
                    (",", COMMA),
                    (0, INT_CONST),
                    (")", RPAREN)
                ],
            ),
            pytest.param(
                "$2 * max(P - 10, 0)",
                [
                    (2, INT_CONST),
                    ("*", MUL),
                    ("max", ID),
                    ("(", LPAREN),
                    ("P", ID),
                    ("-", MINUS),
                    (10, INT_CONST),
                    (",", COMMA),
                    (0, INT_CONST),
                    (")", RPAREN),
                ],
            ),
            pytest.param(
                "@if(A > B, (1 + A) * $100, 0)",
                [
                    ("@if", ID),
                    ("(", LPAREN),
                    ("A", ID),
                    (">", GT),
                    ("B", ID),
                    (",", COMMA),
                    ("(", LPAREN),
                    (1, INT_CONST),
                    ("+", PLUS),
                    ("A", ID),
                    (")", RPAREN),
                    ("*", MUL),
                    (100, INT_CONST),
                    (",", COMMA),
                    (0, INT_CONST),
                    (")", RPAREN),
                ],
            ),
            pytest.param(
                "A > P and B1 == B2 and C1 != C2 and D1 >= D_2 =",
                [
                    ("A", ID),
                    (">", GT),
                    ("P", ID),
                    ("and", AND),
                    ("B1", ID),
                    ("==", EQ2),
                    ("B2", ID),
                    ("and", AND),
                    ("C1", ID),
                    ("!=", NE),
                    ("C2", ID),
                    ("and", AND),
                    ("D1", ID),
                    (">=", GTE),
                    ("D_2", ID),
                    ("==", EQ2),
                ],
            ),
            pytest.param(
                "1...$10",
                [
                    (1.0, FLOAT_CONST),
                    (".", DOT),
                    (".", DOT),
                    (10, INT_CONST),
                ],
            ),
            pytest.param(
                '"str1"+"str2"',
                [
                    ("str1", STR_CONST),
                    ("+", PLUS),
                    ("str2", STR_CONST),
                ]
            ),
            pytest.param(
                'not 1 << 2 | 3 & 4 ^ (~5) // 6 >> 7',
                [
                    ("not", NOT),
                    (1, INT_CONST),
                    ("<<", BIT_LSHIFT),
                    (2, INT_CONST),
                    ("|", BIT_OR),
                    (3, INT_CONST),
                    ("&", BIT_AND),
                    (4, INT_CONST),
                    ("^", BIT_XOR),
                    ("(", LPAREN),
                    ("~", BIT_NOT),
                    (5, INT_CONST),
                    (")", RPAREN),
                    ("//", INT_DIV),
                    (6, INT_CONST),
                    (">>", BIT_RSHIFT),
                    (7, INT_CONST),
                ],
            ),
            pytest.param(
                "1 % 7 ** 8.0 or None or False or not True in",
                [
                    (1, INT_CONST),
                    ("%", MODULO),
                    (7, INT_CONST),
                    ("**", POWER),
                    (8.0, FLOAT_CONST),
                    ("or", OR),
                    (None, CONST),
                    ("or", OR),
                    (False, CONST),
                    ("or", OR),
                    ("not", NOT),
                    (True, CONST),
                    ("in", IN),
                ],
            ),
        ]
    )
    def test_lexer_values(self, expression, expected_result):
        lexer = Lexer(expression)
        res = lexer.all_tokens()

        expected_values = list(map(lambda x: x[0], expected_result))
        expected_types = list(map(lambda x: x[1], expected_result))

        assert expected_values == list(map(attrgetter("value"), res))
        assert expected_types == list(map(attrgetter("type"), res))
