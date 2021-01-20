PLUS = "+"
MINUS = "-"
MULTIPLICATION = "*"
DIVISION = "/"

OPENING_BRACKET = "("
CLOSING_BRACKET = ")"

COMMA = ","

OPERATORS = set([PLUS, MINUS, MULTIPLICATION, DIVISION])
BRACKETS = set([OPENING_BRACKET, CLOSING_BRACKET])
SYMBOLS = set([COMMA, "@"])
WHITESPACES = set([" ", "\t", "\n", "\r"])

def is_digit(c):
    return c >= '0' and c <= '9'

def is_opearator(c):
    return c in OPERATORS

def is_round_bracket(c):
    return c in BRACKETS

def is_name(c):
    return (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z')

def is_symbol(c):
    return c in SYMBOLS

def is_whitespaces(c):
    return c in WHITESPACES

class Lexer:
    def __init__(self, str):
        self.str = str
        self.offset = 0
        self.curr_token = None

    @property
    def curr_token(self):
        return self._curr_token

    @curr_token.setter
    def curr_token(self, value):
        print("set:", value)
        self._curr_token = value

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
            while self.offset < len(self.str) and is_digit(self.str[self.offset]):
                token.append(self.str[self.offset])
                self.offset += 1

            self.curr_token = "".join(token)
            return self.curr_token

        if is_name(c):
            while self.offset < len(self.str) and is_name(self.str[self.offset]):
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

class NumberNode:
    def __init__(self, number):
        self.number = number

    def evaluate(self, _variables):
        return self.number

    def __str__(self):
        return str(self.number)

class VariableNode:
    def __init__(self, name):
        self.name = name

    def evaluate(self, variables):
        if self.name in variables:
            return variables[self.name]
        else:
            raise ParseError("unknown variable: " + self.name)

    def __str__(self):
        return self.name

class OperationNode:
    def __init__(self, operator, left, right=None):
        self.operator = operator
        self.left = left
        self.right = right

    def evaluate(self, variables):
        op1 = self.left.evaluate(variables)
        op2 = self.right.evaluate(variables)

        if self.operator == PLUS:
            return op1 + op2

        if self.operator == MINUS:
            return op1 - op2

        if self.operator == MULTIPLICATION:
            return op1 * op2

        if self.operator == DIVISION:
            return op1 / op2

    def __str__(self):
        return str(self.left) + " " + str(self.operator) + " " + str(self.right)

class FuncNode:
    def __init__(self, arg_nodes, func):
        self.arg_nodes = arg_nodes
        self.func = func

    def evaluate(self, variables):
        args = list(map(lambda node: node.evaluate(variables), self.arg_nodes))
        return self.func(*args)

    def __str__(self):
        return str(self.func.__name__) + "(" + ", ".join(map(str, self.arg_nodes)) + ")"

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, str, const_values=None, func_values=None):
        self.lexer = Lexer(str)
        self.const_values = const_values or {}
        self.func_values = func_values or {}

    def parse(self):
        return self.parse_sum()

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

            if token == MULTIPLICATION:
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
            number = int(token)
            node = NumberNode(number=number)

            token = self.lexer.next_token()
            # if len(token) == 0:
            #     raise ParseError("invalid token: " + token)

            return node

        if is_name(token[0]):
            func = self.func_values.get(token)

            if func:
                token = self.lexer.next_token()
                if token != OPENING_BRACKET:
                    raise ParseError("( is expected, got:" + token)

                arg_nodes = [self.parse_sum()]

                while self.lexer.curr_token == COMMA:
                    arg_nodes.append(self.parse_sum())

                node = FuncNode(arg_nodes=arg_nodes, func=func)

                # breakpoint()
                if self.lexer.curr_token != CLOSING_BRACKET:
                    raise ParseError(") is expected, got:" + token)
                else:
                    self.lexer.next_token()
                    if len(token) == 0:
                        raise ParseError("invalid token: " + token)

                    return node

                return node
            else:
                value = self.const_values.get(token)

                if value:
                    self.lexer.next_token()
                    return NumberNode(number=value)
                else:
                    self.lexer.next_token()
                    return VariableNode(name=token)

        if token == OPENING_BRACKET:
            node = self.parse_sum()
            token = self.lexer.curr_token

            if token != CLOSING_BRACKET:
                raise ParseError(") is expected, got:" + token)
            else:
                self.lexer.next_token()
                if len(token) == 0:
                    raise ParseError("invalid token: " + token)

                return node

        raise ParseError("term is expected")
