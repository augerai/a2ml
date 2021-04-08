import pytest
import re

from a2ml.api.roi.lexer import Lexer
from a2ml.api.roi.parser import Parser
from a2ml.api.roi.validator import AstError, Validator, ValidationError

@pytest.mark.parametrize(
    "expression, expected_result",
    [
        pytest.param("min(1, 2, 3)", True),
        pytest.param("min(1)", "invalid arguments count on 'min' function, expected from 2 to 255 got 1 at position 1"),
        pytest.param("somefunc(1)", "unknown function 'somefunc' at position 1"),
        pytest.param("1 + somefunc(1)", "unknown function 'somefunc' at position 5"),
        pytest.param("max()", "invalid arguments count on 'max' function, expected from 2 to 255 got 0 at position 1"),
        pytest.param("round(1.75)", True),
        pytest.param("$a + $b", True),
        pytest.param("$a + $b + $c", "unknown variable '\$c' at position 11"),
        pytest.param("10 20", "invalid token '20' at position 4"),
        pytest.param("top 1 by from", "unknown atom 'from' at position 10"),
        pytest.param("top 1 by $a from", "unexpected end of expression at position 13"),
    ]
)
def test_validate(expression, expected_result):
    validator = Validator(
        expression,
        known_vars=["$a", "$b"],
    )

    # Validate with force_raise = False
    res = validator.validate(force_raise=False)
    if expected_result == True:
        assert res.is_valid == True
        assert res.error is None
    else:
        assert res.is_valid == False
        assert re.match(expected_result, res.error)

    # Validate with force_raise = True
    if expected_result == True:
        res = validator.validate()
        assert res.is_valid == True
    else:
        with pytest.raises(AstError, match=expected_result):
            result = validator.validate()
