import pytest

from a2ml.api.roi.lexer import Lexer
from a2ml.api.roi.parser import Parser
from a2ml.api.roi.validator import Validator, ValidationError

@pytest.mark.parametrize(
    "expression, expected_result",
    [
        pytest.param("min(1, 2, 3)", True),
        pytest.param("min(1)", "invalid arguments count on 'min' function, expected 2, 3, 4 or 5 got 1 at position 1"),
        pytest.param("somefunc(1)", "unknown function 'somefunc' at position 1"),
        pytest.param("1 + somefunc(1)", "unknown function 'somefunc' at position 5"),
        pytest.param("some_func()", "invalid arguments count on 'some_func' function, expected 1 got 0 at position 1"),
        pytest.param("some_func(1)", True),
        pytest.param("$a + $b", True),
        pytest.param("$a + $b + $c", "unknown variable '\$c' at position 10"),
    ]
)
def test_validate(expression, expected_result):
    parser = Parser(Lexer(expression))
    validator = Validator(
        parser,
        known_vars=["$a", "$b"],
        known_funcs={
            "min": [2, 3, 4, 5],
            "some_func": [1],
        }
    )

    if expected_result == True:
        assert validator.validate() == True
    else:
        with pytest.raises(ValidationError, match=expected_result):
            result = validator.validate()
