import json
import pandas as pd

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
UNDERSCORE = "_"

LT = "<"
EQ = "="
GT = ">"
EXCLAMATION = "!"

NOT = "not"
OR = "or"
AND = "and"

OPERATORS = set([PLUS, MINUS, MULTIPLICATION, DIVISION])
BRACKETS = set([OPENING_BRACKET, CLOSING_BRACKET])
COMPARISON_SYMBOLS = set([LT, EQ, GT, EXCLAMATION])
SYMBOLS = set([COMMA])
WHITESPACES = set([" ", "\t", "\n", "\r"])
NAME_PART = set([AT, DOLLAR, UNDERSCORE])

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
    return (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z') or c in NAME_PART

def is_symbol(c):
    return c in SYMBOLS

def is_whitespaces(c):
    return c in WHITESPACES

class AstError(Exception):
    def __init__(self, msg, position=None):
        self.position = position
        super().__init__(msg)

class LexerError(AstError):
    pass

class Lexer:
    def __init__(self, str):
        self.str = str
        self.reset()

    def reset(self):
        self.offset = 0
        self._curr_token = None
        self.prev_token = None

    @property
    def curr_token(self):
        return self._curr_token

    @curr_token.setter
    def curr_token(self, value):
        self.prev_token = self.curr_token
        self._curr_token = value

    def done(self):
        return self.offset == len(self.str)

    def next_token(self):
        if self.done():
            return None

        c = self.str[self.offset]
        self.offset += 1

        while self.offset < len(self.str) and is_whitespaces(c):
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

        if self.done():
            return None
        else:
            raise LexerError(f"unknown character '{c}'")

    def next_token_preview(self):
        curr_token = self.curr_token
        offset = self.offset

        next_token = self.next_token()

        self.curr_token = curr_token
        self.offset = offset

        return next_token

    def all_tokens(self):
        res = []

        while not self.done():
            res.append(self.next_token())

        return res

class ParserError(AstError):
    pass

class ExpressionError(AstError):
    pass

class BaseNode:
    def __init__(self, position):
        self.position = position

    def has_variables(self):
        return False

    def evaluate_sum(self, rows, vars_mapping={}):
        res = self.evaluate(rows, vars_mapping)
        return sum(res)

class ConstNode(BaseNode):
    def __init__(self, value, position=None):
        super().__init__(position)

        if isinstance(value, float) or isinstance(value, str):
            try:
                number = float(value)
            except ValueError as e:
                raise ParserError(str(e), position=self.position)

            if number.is_integer():
                number = int(number)

            self.value = number
        elif value == True or value == False:
            self.value = value
        else:
            raise ParserError(f"unsupported const type: '{value}'", position=self.position)

    def evaluate(self, rows, vars_mapping={}):
        return [self.value] * len(rows)

    def validate(self, known_vars):
        return True

    def __str__(self):
        return str(self.value)

class VariableNode(BaseNode):
    def __init__(self, name, position=None):
        super().__init__(position)

        if name.startswith("$"):
            self.name = name[1:]
        else:
            self.name = name

    def evaluate(self, rows, vars_mapping={}):
        res = []

        for index, variables in enumerate(rows):
            var_name = vars_mapping.get(self.name, self.name)
            if var_name in variables:
                res.append(variables[var_name])
            else:
                row = json.dumps(variables)

                unknown_var = [self.name]
                if self.name != var_name:
                    unknown_var.append(var_name)
                unknown_var = " -> ".join(unknown_var)

                raise ParserError(
                    f"unknown variable: '{unknown_var}' in row #{index} '{row}'",
                    position=self.position,
                )
        return res

    def validate(self, known_vars):
        if self.name in known_vars:
            return True
        else:
            raise ParserError(f"unknown variable '{self.name}'", position=self.position)

    def has_variables(self):
        return True

    def __str__(self):
        return self.name

class OperationNode(BaseNode):
    def __init__(self, operator, left, right=None, position=None):
        super().__init__(position)

        self.operator = operator
        self.left = left
        self.right = right

    def evaluate(self, rows, vars_mapping={}):
        op1 = self.left.evaluate(rows, vars_mapping)
        op2 = self.right.evaluate(rows, vars_mapping)

        if self.operator == PLUS:
            return [a + b for a, b in zip(op1, op2)]

        if self.operator == MINUS:
            return [a - b for a, b in zip(op1, op2)]

        if self.operator == MULTIPLICATION:
            return [a * b for a, b in zip(op1, op2)]

        if self.operator == DIVISION:
            return [a / b for a, b in zip(op1, op2)]

    def has_variables(self):
        return self.left.has_variables() or self.right.has_variables()

    def validate(self, known_vars):
        return self.left.validate(known_vars) and self.right.validate(known_vars)

    def __str__(self):
        return "(" + str(self.left) + " " + str(self.operator) + " " + str(self.right) + ")"

class FuncNode(BaseNode):
    def __init__(self, arg_nodes, func, position=None):
        super().__init__(position)

        self.arg_nodes = arg_nodes
        self.func = func

    def evaluate(self, rows, vars_mapping={}):
        args_list = [list(map(lambda node: node.evaluate([row], vars_mapping)[0], self.arg_nodes)) for row in rows]

        return [self.func(*args) for args in args_list]

    def has_variables(self):
        return any(map(lambda n: n.has_variables(), self.arg_nodes))

    def validate(self, known_vars):
        return all(map(lambda n: n.validate(known_vars), self.arg_nodes))

    def __str__(self):
        return str(self.func.__name__) + "(" + ", ".join(map(str, self.arg_nodes)) + ")"

class Parser:
    class ValidationResult:
        def __init__(self, is_valid=True, error=None):
            self.is_valid = is_valid
            self.error = error

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
    def logic_and(a, b):
        return a and b

    @staticmethod
    def logic_or(a, b):
        return a or b

    @staticmethod
    def logic_not(a):
        return not a

    @staticmethod
    def logic_if(predicate, true_value, false_value):
        if predicate:
            return true_value
        else:
            return false_value

    FUNC_VALUES = {
        # Math
        "min": min,
        "max": max,
        # Comparison
        "<": lt.__get__(object),
        "<=": le.__get__(object),
        "=": eq.__get__(object),
        ">": gt.__get__(object),
        ">=": ge.__get__(object),
        "!=": ne.__get__(object),
        # Logical
        "and": logic_and.__get__(object),
        "or": logic_or.__get__(object),
        "not": logic_not.__get__(object),
        "@if": logic_if.__get__(object)
    }

    CONST_VALUES = {
        "True": True,
        "False": False,
    }

    def __init__(self, str, const_values=None, func_values=None):
        self.lexer = Lexer(str)
        self.const_values = const_values or self.CONST_VALUES
        self.func_values = func_values or self.FUNC_VALUES

    def parse(self):
        return self.parse_logic_expression()

    def validate(self, force_raise=False, known_vars=[]):
        try:
            tree = self.parse()
            tree.validate(known_vars=known_vars)

            if not self.lexer.done():
                raise ParserError("is not completely parsed")
            else:
                self.lexer.reset()
                return self.ValidationResult()
        except (AstError, ValueError) as e:
            if force_raise:
                raise e
            else:
                position = getattr(e, 'position', None) or self.lexer.offset
                return self.ValidationResult(False, str(e) + f" at position {position}")

    def parse_logic_expression(self, next_token=True):
        left = self.parse_comparison(next_token)
        node = None

        while True:
            token = self.lexer.curr_token

            if token == OR:
                func = self.func_values[token]
                node = FuncNode(func=func, arg_nodes=[node or left, self.parse_logic_expression(next_token)])
            elif token == AND:
                func = self.func_values[token]
                node = FuncNode(func=func, arg_nodes=[node or left, self.parse_comparison(next_token)])
            else:
                return node or left

    def parse_comparison(self, next_token):
        left = self.parse_sum(next_token)
        node = None

        while True:
            token = self.lexer.curr_token

            if token in COMPARISON_OPS:
                if node:
                    left = node

                func = self.func_values[token]
                node = FuncNode(func=func, arg_nodes=[left, self.parse_sum(next_token)])
            else:
                return node or left

    def parse_sum(self, next_token):
        left = self.parse_product(next_token)
        node = None

        while True:
            token = self.lexer.curr_token

            if token == PLUS or token == MINUS:
                if node:
                    node = OperationNode(operator=token[0], left=node, position=self.lexer.offset)
                else:
                    node = OperationNode(operator=token[0], left=left, position=self.lexer.offset)

                node.right = self.parse_product(next_token)
            else:
                if node:
                    return node
                else:
                    return left

    def parse_product(self, next_token):
        left = self.parse_term(next_token)
        node = None

        while True:
            token = self.lexer.curr_token

            if token == MULTIPLICATION or token == DIVISION:
                if node:
                    node = OperationNode(operator=token[0], left=node, position=self.lexer.offset)
                else:
                    node = OperationNode(operator=token[0], left=left, position=self.lexer.offset)

                node.right = self.parse_term(next_token)
            else:
                if node:
                    return node
                else:
                    return left

    def parse_term(self, next_token):
        if next_token:
            token = self.lexer.next_token()
        else:
            token = self.lexer.curr_token

        if token == None:
            raise ParserError(f"unexpected end of expression")

        if len(token) == 0:
            raise ParserError("invalid token: " + token)

        if is_digit(token[0]):
            self.lexer.next_token()
            return ConstNode(token, position=self.lexer.offset - len(token))

        if len(token) > 1 and token[0] == DOLLAR and is_digit(token[1]):
            self.lexer.next_token()
            return ConstNode(token[1:], position=self.lexer.offset - len(token))

        if is_name(token[0]):
            func_token = token
            func = self.func_values.get(token)

            if func:
                token = self.lexer.next_token()
                if token == OPENING_BRACKET:
                    arg_nodes = [self.parse_logic_expression()]

                    while self.lexer.curr_token == COMMA:
                        arg_nodes.append(self.parse_logic_expression())

                    node = FuncNode(arg_nodes=arg_nodes, func=func)

                    if self.lexer.curr_token != CLOSING_BRACKET:
                        raise ParserError(") is expected, got:" + token)
                    else:
                        self.lexer.next_token()
                        if len(token) == 0:
                            raise ParserError("invalid token: " + token)

                        return node

                    return node
                elif self.lexer.prev_token == NOT:
                    # Do not read next token because it's already read
                    return FuncNode(arg_nodes=[self.parse_logic_expression(False)], func=func)
                else:
                    raise ParserError("( is expected, got:" + token)
            else:
                if token in self.const_values:
                    self.lexer.next_token()
                    return ConstNode(self.const_values.get(token), position=self.lexer.offset - len(token))
                elif token == NOT:
                    func = self.func_values[token]
                    return FuncNode(func=func, arg_nodes=[self.parse_logic_expression()])
                else:
                    self.lexer.next_token()

                    if self.lexer.curr_token == OPENING_BRACKET:
                        raise ParserError(f"unknown function '{func_token}'")
                    else:
                        return VariableNode(name=token, position=self.lexer.offset - len(token))

        if token == OPENING_BRACKET:
            node = self.parse_logic_expression()
            token = self.lexer.curr_token

            if token != CLOSING_BRACKET:
                raise ParserError(") is expected, got:" + token)
            else:
                self.lexer.next_token()
                if len(token) == 0:
                    raise ParserError("invalid token: " + token)

                return node

        raise ParserError("term is expected, got: " + token)

class Calculator:
    def __init__(self, revenue=None, investment=None, filter=None, known_vars=[], vars_mapping={}):
        self.revenue = revenue
        self.investment = investment
        self.filter = filter
        self.known_vars = known_vars + list(vars_mapping.keys())
        self.vars_mapping = vars_mapping

        self.revenue_ast = self.build_ast(self.revenue)
        self.investment_ast = self.build_ast(self.investment)
        self.filter_ast = self.build_ast(self.filter)

    def build_ast(self, expression):
        if expression:
            parser = Parser(expression)
            parser.validate(force_raise=True, known_vars=self.known_vars)
            return parser.parse()

    def calculate(self, rows):
        if isinstance(rows, pd.DataFrame):
            rows = list(map(lambda x: x[1].to_dict(), rows.iterrows()))

        filtered_rows = rows

        if self.filter_ast:
            filtered_rows = [row for row, marked in zip(rows, self.filter_ast.evaluate(rows, self.vars_mapping)) if marked]

        revenue = self.revenue_ast.evaluate_sum(filtered_rows, self.vars_mapping)
        investment = self.investment_ast.evaluate_sum(filtered_rows, self.vars_mapping)
        roi = (revenue - investment) / investment

        return {
            "count": len(filtered_rows),
            "filtered_rows": filtered_rows,
            "revenue": revenue,
            "investment": investment,
            "roi": roi,
        }
