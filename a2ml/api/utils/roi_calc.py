import json

PLUS = "+"
MINUS = "-"
MULTIPLICATION = "*"
DIVISION = "/"

OPENING_BRACKET = "("
CLOSING_BRACKET = ")"

COMMA = ","
AT = "@"
DOLLAR = "$"
DOT = "."

LT = "<"
EQ = "="
GT = ">"
EXCLAMATION = "!"

OPERATORS = set([PLUS, MINUS, MULTIPLICATION, DIVISION])
BRACKETS = set([OPENING_BRACKET, CLOSING_BRACKET])
COMPARISON_SYMBOLS = set([LT, EQ, GT, EXCLAMATION])
SYMBOLS = set([COMMA])
WHITESPACES = set([" ", "\t", "\n", "\r"])

COMPARISON_OPS = set(["<", ">", "<=", ">=", "=", "!="])

def is_digit(c):
    return c >= '0' and c <= '9'

def is_decimal_separator(c):
    return c == DOT

def is_opearator(c):
    return c in OPERATORS

def is_comparison_sym(c):
    return c in COMPARISON_SYMBOLS

def is_round_bracket(c):
    return c in BRACKETS

def is_name(c):
    return (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z') or c == AT or c == DOLLAR

def is_symbol(c):
    return c in SYMBOLS

def is_whitespaces(c):
    return c in WHITESPACES

class Lexer:
    def __init__(self, str):
        self.str = str
        self.offset = 0
        self.curr_token = None

    def done(self):
        return self.offset == len(self.str)

    def next_token(self):
        if self.done():
            return None

        c = self.str[self.offset]
        self.offset += 1

        while is_whitespaces(c):
            c = self.str[self.offset]
            self.offset += 1

        if is_opearator(c) or is_round_bracket(c) or is_symbol(c):
            self.curr_token = c
            return self.curr_token

        token = [c]

        if is_digit(c):
            while self.offset < len(self.str) and (is_digit(self.str[self.offset]) or is_decimal_separator(self.str[self.offset])):
                token.append(self.str[self.offset])
                self.offset += 1

            self.curr_token = "".join(token)
            return self.curr_token

        if is_name(c):
            while self.offset < len(self.str) and (is_name(self.str[self.offset]) or is_digit(self.str[self.offset])):
                token.append(self.str[self.offset])
                self.offset += 1

            self.curr_token = "".join(token)
            return self.curr_token

        if is_comparison_sym(c):
            while self.offset < len(self.str) and is_comparison_sym(self.str[self.offset]):
                token.append(self.str[self.offset])
                self.offset += 1

            self.curr_token = "".join(token)
            return self.curr_token

        return None

    def all_tokens(self):
        res = []

        while not self.done():
            res.append(self.next_token())

        return res
class ParseError(Exception):
    pass

class BaseNode:
    def has_aggregation(self):
        return False

    def evaluate_scalar(self, rows):
        res = self.evaluate(rows)

        if self.has_aggregation():
            return res[0]
        else:
            return sum(res)

class NumberNode(BaseNode):
    def __init__(self, token):
        number = float(token)

        if number.is_integer():
            number = int(number)

        self.number = number

    def evaluate(self, rows):
        return [self.number] * len(rows)

    def __str__(self):
        return str(self.number)

class VariableNode(BaseNode):
    def __init__(self, name):
        self.name = name

    def evaluate(self, rows):
        res = []

        for index, variables in enumerate(rows):
            if self.name in variables:
                res.append(variables[self.name])
            else:
                row = json.dumps(variables)
                raise ParseError(f"unknown variable: '{self.name}' in row #{index} '{row}'")
        return res

    def __str__(self):
        return self.name

class OperationNode(BaseNode):
    def __init__(self, operator, left, right=None):
        self.operator = operator
        self.left = left
        self.right = right

    def evaluate(self, rows):
        op1 = self.left.evaluate(rows)
        op2 = self.right.evaluate(rows)

        if self.operator == PLUS:
            return [a + b for a, b in zip(op1, op2)]

        if self.operator == MINUS:
            return [a - b for a, b in zip(op1, op2)]

        if self.operator == MULTIPLICATION:
            return [a * b for a, b in zip(op1, op2)]

        if self.operator == DIVISION:
            return [a / b for a, b in zip(op1, op2)]

    def has_aggregation(self):
        return self.left.has_aggregation() or self.right.has_aggregation()

    def __str__(self):
        return "(" + str(self.left) + " " + str(self.operator) + " " + str(self.right) + ")"

class FuncNode(BaseNode):
    def __init__(self, arg_nodes, func, agg=False):
        self.arg_nodes = arg_nodes
        self.func = func
        self.agg = agg

    def evaluate(self, rows):
        # breakpoint()
        # args_list = list(map(lambda node: node.evaluate(rows), self.arg_nodes))
        # args_list = [node.evaluate(rows) for node in self.arg_nodes]
        args_list = [list(map(lambda node: node.evaluate([row])[0], self.arg_nodes)) for row in rows]

        if self.agg:
            return [self.func(args_list)] * len(rows)
        else:
            return [self.func(*args) for args in args_list]

    def has_aggregation(self):
        return self.agg or any(map(lambda n: n.has_aggregation(), self.arg_nodes))

    def __str__(self):
        return str(self.func.__name__) + "(" + ", ".join(map(str, self.arg_nodes)) + ")"

class Parser:
    def __init__(self, str, const_values=None, func_values=None):
        self.lexer = Lexer(str)
        self.const_values = const_values or {}
        self.func_values = func_values or {}

    def parse(self):
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_sum()
        node = None

        while True:
            token = self.lexer.curr_token

            if token in COMPARISON_OPS:
                if node:
                    left = node

                func = self.func_values[token]
                node = FuncNode(func=func, arg_nodes=[left, self.parse_sum()])
            else:
                return node or left

    def parse_sum(self):
        left = self.parse_product()
        node = None

        while True:
            token = self.lexer.curr_token

            if token == PLUS or token == MINUS:
                if node:
                    node = OperationNode(operator=token[0], left=node)
                else:
                    node = OperationNode(operator=token[0], left=left)

                node.right = self.parse_product()
            else:
                if node:
                    return node
                else:
                    return left

    def parse_product(self):
        left = self.parse_term()
        node = None

        while True:
            token = self.lexer.curr_token

            if token == MULTIPLICATION or token == DIVISION:
                if node:
                    node = OperationNode(operator=token[0], left=node)
                else:
                    node = OperationNode(operator=token[0], left=left)

                node.right = self.parse_term()
            else:
                if node:
                    return node
                else:
                    return left

    def parse_term(self):
        token = self.lexer.next_token()
        if len(token) == 0:
            raise ParseError("invalid token: " + token)

        if is_digit(token[0]):
            self.lexer.next_token()
            return NumberNode(token)

        if len(token) > 1 and token[0] == DOLLAR and is_digit(token[1]):
            self.lexer.next_token()
            return NumberNode(token[1:])

        if is_name(token[0]):
            func_token = token
            func = self.func_values.get(token)

            if func:
                token = self.lexer.next_token()
                if token == OPENING_BRACKET:
                    arg_nodes = [self.parse_comparison()]

                    while self.lexer.curr_token == COMMA:
                        arg_nodes.append(self.parse_comparison())

                    node = FuncNode(arg_nodes=arg_nodes, func=func, agg=func_token[0] == AT)

                    if self.lexer.curr_token != CLOSING_BRACKET:
                        raise ParseError(") is expected, got:" + token)
                    else:
                        self.lexer.next_token()
                        if len(token) == 0:
                            raise ParseError("invalid token: " + token)

                        return node

                    return node
                elif func_token[0] == AT:
                    # Allow agg func without brackets (empty parameters)
                    return FuncNode(arg_nodes=[], func=func, agg=True)
                else:
                    raise ParseError("( is expected, got:" + token)
            else:
                value = self.const_values.get(token)

                if value:
                    self.lexer.next_token()
                    return NumberNode(value)
                else:
                    self.lexer.next_token()
                    return VariableNode(name=token)

        if token == OPENING_BRACKET:
            node = self.parse_comparison()
            token = self.lexer.curr_token

            if token != CLOSING_BRACKET:
                raise ParseError(") is expected, got:" + token)
            else:
                self.lexer.next_token()
                if len(token) == 0:
                    raise ParseError("invalid token: " + token)

                return node

        raise ParseError("term is expected, got: " + token)

class RoiCalculator:
    @staticmethod
    def lt(a, b):
        return a < b

    def le(a, b):
        return a <= b

    @staticmethod
    def eq(a, b):
        return a == b

    @staticmethod
    def gt(a, b):
        return a > b

    @staticmethod
    def ge(a, b):
        return a >= b

    @staticmethod
    def ne(a, b):
        return a != b

    @staticmethod
    def sum(value_and_predicate):
        res = 0

        for item in value_and_predicate:
            predicate = True
            value = item[0]

            if len(item) == 2:
                value, predicate = item

            if predicate:
                res += value

        return res

    @staticmethod
    def count(value_and_predicate):
        res = 0

        for item in value_and_predicate:
            predicate = True

            if len(item) == 2:
                _, predicate = item

            if predicate:
                res += 1

        return res

    FUNC_VALUES = {
        "min": min,
        "max": max,
        "<": lt.__get__(object),
        "<=": le.__get__(object),
        "=": eq.__get__(object),
        ">": gt.__get__(object),
        ">=": ge.__get__(object),
        "!=": ne.__get__(object),
        "@sum": sum.__get__(object),
        "@count": count.__get__(object),
    }

    CONST_VALUES = {
        "True": True,
        "False": False,
    }

    def __init__(self, revenue=None, investment=None, filter=None):
        self.revenue = revenue
        self.investment = investment
        self.filter = filter

        self.revenue_ast = self.build_ast(self.revenue)
        self.investment_ast = self.build_ast(self.investment)
        self.filter_ast = self.build_ast(self.filter)

    def build_ast(self, expression):
        if expression:
            parser = Parser(expression, const_values=self.CONST_VALUES, func_values=self.FUNC_VALUES)
            return parser.parse()

    def calculate(self, rows):
        filtered_rows = rows

        if self.filter_ast:
            filtered_rows = [row for row, marked in zip(rows, self.filter_ast.evaluate(rows)) if marked]

        revenue = self.revenue_ast.evaluate_scalar(filtered_rows)
        investment = self.investment_ast.evaluate_scalar(filtered_rows)
        roi = (revenue - investment) / investment

        return {
            "count": len(filtered_rows),
            "filtered_rows": filtered_rows,
            "revenue": revenue,
            "investment": investment,
            "roi": roi,
        }
