import pandas as pd

from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser
from .validator import Validator
from .var_names_fetcher import VarNamesFetcher


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
            filtered_rows = self.filter_interpreter.run(rows, filter=True)

        if len(filtered_rows) > 0:
            revenue = sum(self.revenue_interpreter.run(filtered_rows))
            investment = sum(self.investment_interpreter.run(filtered_rows))
        else:
            revenue = 0
            investment = 0

        if investment > 0:
            roi = (revenue - investment) / investment
        else:
            roi = 0

        return {
            "count": len(filtered_rows),
            "filtered_rows": filtered_rows,
            "revenue": revenue,
            "investment": investment,
            "roi": roi,
        }

    def get_var_names(self):
        result = []
        if self.revenue:
            fetcher = VarNamesFetcher(self.revenue)
            result += fetcher.fetch()

        if self.investment:
            fetcher = VarNamesFetcher(self.investment)
            result += fetcher.fetch()

        if self.filter:
            fetcher = VarNamesFetcher(self.filter)
            result += fetcher.fetch()

        result = set(result)    
        return [var[1:] for var in result if var.startswith('$')]
