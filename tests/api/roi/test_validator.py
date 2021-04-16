import pytest
import re

from a2ml.api.roi.lexer import Lexer
from a2ml.api.roi.parser import Parser
from a2ml.api.roi.validator import AstError, Validator, ValidationError

@pytest.mark.parametrize(
    "expression, expected_result, message",
    [
        pytest.param("min(1, 2, 3)", True, None),
        pytest.param("min(1)", "error", "invalid arguments count on 'min' function, expected from 2 to 255 got 1 at position 1"),
        pytest.param("somefunc(1)", "error", "unknown function 'somefunc' at position 1"),
        pytest.param("1 + somefunc(1)", "error", "unknown function 'somefunc' at position 5"),
        pytest.param("max()", "error", "invalid arguments count on 'max' function, expected from 2 to 255 got 0 at position 1"),
        pytest.param("round(1.75)", True, None),
        pytest.param("$a + $b", True, None),
        pytest.param("$a + $b + $c", "warning", "unknown variable '\$c' at position 11"),
        pytest.param("10 20", "error", "invalid token '20' at position 4"),
        pytest.param("top 1 by from", "error", "unknown atom 'from' at position 10"),
        pytest.param("top 1 by $a from", "error", "unexpected end of expression at position 13"),
    ]
)
def test_validate(expression, expected_result, message):
    validator = Validator(
        expression,
        known_vars=["$a", "$b"],
    )

    # Validate with force_raise = False
    res = validator.validate(force_raise=False)
    if expected_result == True:
        assert res.is_valid == True
        assert res.error is None
        assert res.warning is None
    elif expected_result == "warning":
        assert res.is_valid == True
        assert re.match(message, res.warning)
    elif expected_result == "error":
        assert res.is_valid == False
        assert re.match(message, res.error)
    else:
        raise ValueError(expected_result)

    # Validate with force_raise = True
    if expected_result == True:
        res = validator.validate()
    elif expected_result == "warning":
        assert res.is_valid == True
        res = validator.validate()
        assert re.match(message, res.warning)
    elif expected_result == "error":
        with pytest.raises(AstError, match=message):
            result = validator.validate()
    else:
        raise ValueError(expected_result)
