import pandas as pd

from a2ml.api.roi.calculator import Calculator

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
