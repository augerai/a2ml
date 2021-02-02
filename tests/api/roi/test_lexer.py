import pytest
from a2ml.api.roi.lexer import Lexer

class TestLexer():
    @pytest.mark.parametrize(
        "expression, exected_result",
        [
            pytest.param(
                "$2*max(P-10,0)",
                [2, "*", "max", "(", "P", "-", 10, ",", 0, ")"],
            ),
            pytest.param(
                "$2 * max(P - 10, 0)",
                [2, "*", "max", "(", "P", "-", 10, ",", 0, ")"],
            ),
            pytest.param(
                "@if(A > B, (1 + A) * $100, 0)",
                ["@if", "(", "A", ">", "B", ",", "(", 1, "+", "A", ")", "*", 100, ",", 0, ")"],
            ),
            pytest.param(
                "A > P and B1 == B2 and C1 != C2 and D1 >= D_2",
                ["A", ">", "P", "and", "B1", "==", "B2", "and", "C1", "!=", "C2", "and", "D1", ">=", "D_2"],
            ),
            pytest.param(
                "1...$10",
                [1.0, ".", ".", 10],
            ),
            pytest.param(
                '"str1"+"str2"',
                ["str1", "+", "str2"]
            ),
            pytest.param(
                'not 1 << 2 | 3 & 4 ^ (~5) // 6',
                ["not", 1, "<<", 2, "|", 3, "&", 4, "^", "(", "~", 5, ")", "//", 6],
            ),
            pytest.param(
                "1 % 7 ** 8 or None or False or not True",
                [1, "%", 7, "**", 8, "or", "None", "or", "False", "or", "not", "True"],
            ),
        ]
    )
    def test_lexer(self, expression, exected_result):
        lexer = Lexer(expression)
        res = lexer.all_tokens()

        assert exected_result == res
