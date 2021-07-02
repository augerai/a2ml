import pytest
import re

from a2ml.api.roi.lexer import Lexer
from a2ml.api.roi.parser import Parser
from a2ml.api.roi.var_names_fetcher import VarNamesFetcher

@pytest.mark.parametrize(
    "expression, expected_result",
    [
        pytest.param("min(1, 2, 3)", []),
        pytest.param("min($a, $b, $c)", ["$a", "$b", "$c"]),
        pytest.param("$a + $b", ["$a", "$b"]),
        pytest.param("P > 0.4 and top 5 by P", ["P"]),
        pytest.param("all with agg_max(P) as max_p, agg_min(P) as min_p per $a", ["P", "$a"]),
    ]
)
def test_fetch(expression, expected_result):
    fetcher = VarNamesFetcher(expression)

    result = fetcher.fetch()
    result.sort()
    expected_result.sort()

    assert result == expected_result
