import math
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
        pytest.param("ceil(1.2)", 2),
        pytest.param("floor(1.2)", 1),
        pytest.param("exp(5)", math.exp(5)),
        pytest.param("log(5)", math.log(5)),
        pytest.param("log(4, 2)", 2),
        pytest.param("log2(5)", math.log2(5)),
        pytest.param("log10(5)", math.log10(5)),
        pytest.param("$price * 1.4 - $12", 58),
        pytest.param("($price * 1.4 - $12) * (1 - $taxes)", 49.3),
        pytest.param("($price * $1.4 - A) * (1 - $taxes)", 51),
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
        pytest.param("$a + $b > 5", [False, True]),
    ]
)
def test_interpreter_with_list(expression, exected_result):
    variables = [
        { "$a": 2, "$b": 3 },
        { "$a": 4, "$b": 6 },
    ]

    interpreter = Interpreter(expression)

    assert interpreter.run(variables) == exected_result

@pytest.mark.parametrize(
    "expression, exected_result",
    [
        pytest.param(
            "top 1 by P per $symbol",
            [
                { "P": 0.9, "$symbol": "A", "$spread": 0.5 },
                { "P": 0.7, "$symbol": "T", "$spread": 1 },
            ],
        ),
        pytest.param(
            "bottom 1 by P per $symbol",
            [
                { "P": 0.5, "$symbol": "A", "$spread": 0.9 },
                { "P": 0.6, "$symbol": "T", "$spread": 0.5 },
            ],
        ),
        pytest.param(
            "top 2 by P from (bottom 1 by $spread per $symbol)",
            [
                { "P": 0.9, "$symbol": "A", "$spread": 0.5 },
                { "P": 0.6, "$symbol": "T", "$spread": 0.5 },
            ],
        ),
        pytest.param(
            "top 2 by P from (bottom 1 by $spread per $symbol where P > 0.7)",
            [{ "P": 0.9, "$symbol": "A", "$spread": 0.5 }],
        ),
        pytest.param(
            'top 3 by P - $spread / 2 per $symbol < "Z" where P ** 2 > 0',
            [
                { "P": 0.9, "$symbol": "A", "$spread": 0.5 },
                { "P": 0.6, "$symbol": "T", "$spread": 0.5 },
                { "P": 0.7, "$symbol": "A", "$spread": 0.8 },
            ],
        ),
        pytest.param(
            'all with agg_max(P) per $symbol',
            [
                { "P": 0.6, "$symbol": "T", "$spread": 0.5, "agg_max(P)": 0.7 },
                { "P": 0.7, "$symbol": "T", "$spread": 1, "agg_max(P)": 0.7 },
                { "P": 0.9, "$symbol": "A", "$spread": 0.5, "agg_max(P)": 0.9 },
                { "P": 0.5, "$symbol": "A", "$spread": 0.9, "agg_max(P)": 0.9 },
                { "P": 0.7, "$symbol": "A", "$spread": 0.8, "agg_max(P)": 0.9 },
            ]
        ),
    ]
)
def test_interpreter_top_expressions(expression, exected_result):
    variables = [
        { "P": 0.6, "$symbol": "T", "$spread": 0.5 },
        { "P": 0.7, "$symbol": "T", "$spread": 1 },
        { "P": 0.9, "$symbol": "A", "$spread": 0.5 },
        { "P": 0.5, "$symbol": "A", "$spread": 0.9 },
        { "P": 0.7, "$symbol": "A", "$spread": 0.8 },
    ]

    interpreter = Interpreter(expression)

    assert interpreter.run(variables) == exected_result

def test_interpreter_top_expression_with_tuples():
    expression = """
        top 1 by max_p per $date from (
            top 1 by P per ($symbol, $date) where $close_ask<4 and $close_ask>=0.1
            from (
                all with agg_max(P) as max_p per ($symbol, $date)
            )
        )
    """

    variables = [
        { "$close_ask": 1, "P": 0.6, "$symbol": "T", "$date": "2021-07-05" },
        { "$close_ask": 1, "P": 0.7, "$symbol": "T", "$date": "2021-07-05" }, #
        { "$close_ask": 0, "P": 0.9, "$symbol": "A", "$date": "2021-07-05" },
        { "$close_ask": 1, "P": 0.5, "$symbol": "A", "$date": "2021-07-05" },
        { "$close_ask": 1, "P": 0.7, "$symbol": "A", "$date": "2021-07-05" }, #

        { "$close_ask": 1, "P": 0.7, "$symbol": "T", "$date": "2021-07-06" },
        { "$close_ask": 1, "P": 0.8, "$symbol": "T", "$date": "2021-07-06" }, #
        { "$close_ask": 1, "P": 0.7, "$symbol": "A", "$date": "2021-07-06" }, #
        { "$close_ask": 1, "P": 0.5, "$symbol": "A", "$date": "2021-07-06" },
        { "$close_ask": 0, "P": 1.0, "$symbol": "A", "$date": "2021-07-06" },
    ]

    interpreter = Interpreter(expression)

    assert interpreter.run(variables) == [
        { "$close_ask": 1, "P": 0.7, "$symbol": "A", "$date": "2021-07-06", "max_p": 1.0 },
        { "$close_ask": 1, "P": 0.7, "$symbol": "A", "$date": "2021-07-05", "max_p": 0.9 },
    ]

def test_interpreter_and_with_nones():
    expression = "all where $delta != None and ($delta > 0.1)"

    variables = [
        { "$id": 0, "$delta": 0 },
        { "$id": 1, "$delta": None },
        { "$id": 2, "$delta": 0.1 },
        { "$id": 3, "$delta": 0.2 },
    ]

    interpreter = Interpreter(expression)

    assert interpreter.run(variables) == [
        { "$id": 3, "$delta": 0.2 },
    ]
