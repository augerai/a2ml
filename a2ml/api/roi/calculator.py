import pandas as pd

from a2ml.api.roi.interpreter import Interpreter
from a2ml.api.roi.lexer import Lexer
from a2ml.api.roi.parser import Parser
from a2ml.api.roi.validator import Validator

class Calculator:
    def __init__(self, revenue=None, investment=None, filter=None, known_vars=[], vars_mapping={}):
        self.revenue = revenue
        self.investment = investment
        self.filter = filter
        self.known_vars = known_vars + list(vars_mapping.keys())
        self.vars_mapping = vars_mapping

        self.revenue_interpreter = self.build_interpreter(self.revenue)
        self.investment_interpreter = self.build_interpreter(self.investment)
        self.filter_interpreter = self.build_interpreter(self.filter)

    def build_interpreter(self, expression):
        if expression:
            return Interpreter(expression, self.vars_mapping)

    def calculate(self, rows):
        if isinstance(rows, pd.DataFrame):
            rows = list(map(lambda x: x[1].to_dict(), rows.iterrows()))

        filtered_rows = rows

        if self.filter_interpreter:
            filtered_rows = [row for row, marked in zip(rows, self.filter_interpreter.run(rows)) if marked]

        revenue = sum(self.revenue_interpreter.run(filtered_rows))
        investment = sum(self.investment_interpreter.run(filtered_rows))
        roi = (revenue - investment) / investment

        return {
            "count": len(filtered_rows),
            "filtered_rows": filtered_rows,
            "revenue": revenue,
            "investment": investment,
            "roi": roi,
        }
