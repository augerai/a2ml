import pandas as pd
import pytest

from a2ml.api.roi.calculator import Calculator
from a2ml.api.roi.interpreter import MissedVariable

class TestCalculator:
    def test_options_app(self):
        calc = Calculator(
            filter="P >= 0.2",
            revenue="(1 + A) * $100",
            investment="$100",
            known_vars=["A", "P"],
        )

        res = calc.calculate(
            [
                {"A": 0.1, "P": 0.1},
                {"A": 0.1, "P": 0.15},
                {"A": 0.5, "P": 0.2},
                {"A": 0.3, "P": 0.3},
            ]
        )

        assert 2 == res["count"]
        assert res["filtered_rows"] == [
            {"A": 0.5, "P": 0.2},
            {"A": 0.3, "P": 0.3},
        ]

        assert (0.5 + 0.3 + 2) * 100 == res["revenue"]
        assert 200 == res["investment"]
        assert 0.4 == res["roi"]

    def test_options_app_with_top(self):
        calc = Calculator(
            filter="top 2 by P where P >= 0.1 from (bottom 1 by $spread per $symbol)",
            revenue="(1 + A) * $100",
            investment="$100",
            known_vars=["A", "P", "spread", "symbol"],
        )

        res = calc.calculate(
            [
                {"A": 0.1, "P": 0.10, "$spread": 0.3, "$symbol": "A"},
                {"A": 0.1, "P": 0.15, "$spread": 0.4, "$symbol": "A"},
                {"A": 0.5, "P": 0.20, "$spread": 0.5, "$symbol": "T"},
                {"A": 0.3, "P": 0.30, "$spread": 0.3, "$symbol": "T"},
            ]
        )

        assert 2 == res["count"]
        assert res["filtered_rows"] == [
            {"A": 0.3, "P": 0.30, "$spread": 0.3, "$symbol": "T"},
            {"A": 0.1, "P": 0.10, "$spread": 0.3, "$symbol": "A"},
        ]

        assert (0.1 + 0.3 + 2) * 100 == res["revenue"]
        assert 200 == res["investment"]
        assert 0.2 == res["roi"]

    # def test_options_app_with_top_having(self):
    #     known_vars=["A", "P", "spread", "symbol"]
    #     vars_mapping = {}
    #     for known_var in known_vars:
    #         vars_mapping["$" + known_var] = known_var

    #     calc = Calculator(
    #         # filter="top 2 by P from (top 1 by P per $symbol having min($spread)<0.4) order by P desc",
    #         filter="top 2 by P from (top 1 by P per $symbol) order by P desc",
    #         revenue="(1 + A) * $100",
    #         investment="$100",
    #         known_vars=known_vars,
    #         vars_mapping=vars_mapping,
    #     )

    #     res = calc.calculate(
    #         [
    #             {"A": 0.1, "P": 0.10, "spread": 0.3, "symbol": "A"},
    #             {"A": 0.1, "P": 0.15, "spread": 0.4, "symbol": "A"},
    #             {"A": 0.5, "P": 0.20, "spread": 0.5, "symbol": "T"},
    #             {"A": 0.5, "P": 0.80, "spread": 0.1, "symbol": "T"},
    #             {"A": 0.3, "P": 0.30, "spread": 0.3, "symbol": "T"},
    #         ]
    #     )

    #     assert 2 == res["count"]
    #     assert res["filtered_rows"] == [
    #         {"A": 0.5, "P": 0.80, "spread": 0.1, "symbol": "T"},
    #         {"A": 0.1, "P": 0.10, "spread": 0.3, "symbol": "A"},
    #     ]

    def test_options_app_with_missing_values(self):
        calc = Calculator(
            filter="top 2 by P where P >= 0.1 from (bottom 1 by $spread per $symbol)",
            revenue="(1 + A) * $100",
            investment="$100",
            known_vars=["A", "P", "spread", "symbol"],
        )

        with pytest.raises(MissedVariable, match='missed var `\$symbol` in row `{"A": 0.3, "P": 0.3, "\$spread": 0.3}'):
            calc.calculate(
                [
                    {"A": 0.1, "P": 0.10, "$symbol": "A"},
                    {"A": 0.1, "P": 0.15, "$spread": 0.4, "$symbol": "A"},
                    {"A": 0.5, "P": 0.20, "$spread": 0.5, "$symbol": "T"},
                    {"A": 0.3, "P": 0.30, "$spread": 0.3},
                ]
            )

    def test_bike_rental(self):
        calc = Calculator(
            revenue="min(A, P) * $10",
            investment="$2 * max(P - 10, 0)",
            known_vars=["A", "P"],
        )

        res = calc.calculate(
            [
                {"A": 10, "P": 5},
                {"A": 10, "P": 10},
                {"A": 10, "P": 15},
                {"A": 20, "P": 15},
            ]
        )

        assert 4 == res["count"]
        assert res["filtered_rows"] == [
            {"A": 10, "P": 5},
            {"A": 10, "P": 10},
            {"A": 10, "P": 15},
            {"A": 20, "P": 15},
        ]

        assert (5 + 10 + 10 + 15) * 10 == res["revenue"]
        assert (0 + 0 + 5 + 5) * 2 == res["investment"]
        assert 19 == res["roi"]

    def test_credit_analysis(self):
        calc = Calculator(
            filter="P=True",
            revenue="if(A=True, $1050, $0)",
            investment="$1000",
            known_vars=["A", "P"],
        )

        res = calc.calculate(
            [
                {"A": True, "P": True},
                {"A": True, "P": False},
                {"A": False, "P": True},
                {"A": False, "P": False},
            ]
        )

        assert 2 == res["count"]
        assert res["filtered_rows"] == [
            {"A": True, "P": True},
            {"A": False, "P": True},
        ]

        assert 1050 == res["revenue"]
        assert 2000 == res["investment"]
        assert -0.475 == res["roi"]

    def test_credit_analysis_zero_div(self):
        calc = Calculator(
            filter="P=True",
            revenue="if(A=True, $1050, $0)",
            investment="$1000",
            known_vars=["A", "P"],
        )

        res = calc.calculate(
            [
                {"A": True, "P": False},
                {"A": False, "P": False},
            ]
        )

        assert 0 == res["count"]
        assert res["filtered_rows"] == []

        assert 0 == res["revenue"]
        assert 0 == res["investment"]
        assert 0 == res["roi"]

    def test_credit_analysis_with_pandas_df(self):
        calc = Calculator(
            filter="P=True",
            revenue="if(A=True, $1050, $0)",
            investment="$1000",
            known_vars=["a2ml_actual", "class"],
            vars_mapping={"A": "a2ml_actual", "P": "class"}
        )

        res = calc.calculate(
            pd.DataFrame(
                [
                    {"a2ml_actual": True, "class": True},
                    {"a2ml_actual": True, "class": False},
                    {"a2ml_actual": False, "class": True},
                    {"a2ml_actual": False, "class": False},
                ]
            )
        )

        assert 2 == res["count"]
        assert res["filtered_rows"] == [
            {"a2ml_actual": True, "class": True},
            {"a2ml_actual": False, "class": True},
        ]

        assert 1050 == res["revenue"]
        assert 2000 == res["investment"]
        assert -0.475 == res["roi"]

    def test_with_non_known_var(self):
        calc = Calculator(
            filter="",
            revenue="$revenue",
            investment="$cost",
            known_vars=["revenue"], # cost is non known (not in features but in dataset)
        )

        res = calc.calculate(
            [
                {"revenue": 5, "cost": 1},
                {"revenue": 10, "cost": 2},
            ]
        )

        assert 2 == res["count"]
        assert res["filtered_rows"] == [
            {"revenue": 5, "cost": 1},
                {"revenue": 10, "cost": 2},
        ]

        assert 15 == res["revenue"]
        assert 3 == res["investment"]
        assert 4 == res["roi"]
