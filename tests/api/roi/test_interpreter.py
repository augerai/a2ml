import pytest

from a2ml.api.roi.lexer import Lexer
from a2ml.api.roi.parser import Parser
from a2ml.api.roi.interpreter import Interpreter

@pytest.mark.parametrize(
    "expression, exected_result",
    [
        pytest.param("3 / 2", 1.5),
        pytest.param("3 // 2", 1),
        pytest.param("8 % 3", 2),
        pytest.param("2 ** 4", 16),
        pytest.param("2 > 1 and 2 <= 2", True),
        pytest.param("2 < 1 or 2 >= 2", True),
        pytest.param("2 == 2 and 1 = 1", True),
        pytest.param("3 != 1 + 2", False),
        pytest.param("3 ^ 4", 3 ^ 4),
        pytest.param("3 | 6", 3 | 6),
        pytest.param("3 & 6", 3 & 6),
        pytest.param("3 & 6", 3 & 6),
        pytest.param("3 << 2", 3 << 2),
        pytest.param("100 >> 1", 100 >> 1),
        pytest.param("+2 + -3", -1),
        pytest.param("~5", ~5),
        pytest.param("$price * 1.4 - $12", 58),
        pytest.param("($price * 1.4 - $12) * (1 - $taxes)", 49.3),
        pytest.param("($price * 1.4 - A) * (1 - $taxes)", 51),
        pytest.param("if($price > $100, $taxes + 0.1, $taxes + 0.05)", 0.2),
    ]
)
def test_feature_values(expression, exected_result):
    variables = {
        "$price": 50,
        "$taxes": 0.15,
        "A": 10,
    }

    tree = Parser(Lexer(expression)).parse()
    interpreter = Interpreter(tree, variables)

    assert interpreter.run() == exected_result
