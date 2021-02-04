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
        pytest.param("min(1, 2, 3)", 1),
        pytest.param("max(1, 2, 3)", 3),
        pytest.param("abs(-1.5)", 1.5),
        pytest.param('len("some string")', 11),
        pytest.param("round(1.23456)", 1),
        pytest.param("round(1.23456, 3)", 1.235),
        pytest.param("$price * 1.4 - $12", 58),
        pytest.param("($price * 1.4 - $12) * (1 - $taxes)", 49.3),
        pytest.param("($price * 1.4 - A) * (1 - $taxes)", 51),
        pytest.param("if($price > $100, $taxes + 0.1, $taxes + 0.05)", 0.2),
    ]
)
def test_interpreter_with_scalar(expression, exected_result):
    variables = {
        "$price": 50,
        "$taxes": 0.15,
        "A": 10,
    }

    interpreter = Interpreter(expression)

    assert interpreter.run(variables) == exected_result

@pytest.mark.parametrize(
    "expression, exected_result",
    [
        pytest.param("random()", (0, 1)),
        pytest.param("randint(1, 10)", (1, 10)),
    ]
)
def test_interpreter_random_func(expression, exected_result):
    interpreter = Interpreter(expression)

    res = interpreter.run()

    assert res >= exected_result[0]
    assert res <= exected_result[1]


@pytest.mark.parametrize(
    "expression, exected_result",
    [
        pytest.param("$a + $b", [5, 10]),
    ]
)
def test_interpreter_with_list(expression, exected_result):
    variables = [
        { "$a": 2, "$b": 3 },
        { "$a": 4, "$b": 6 },
    ]

    interpreter = Interpreter(expression)

    assert interpreter.run(variables) == exected_result
