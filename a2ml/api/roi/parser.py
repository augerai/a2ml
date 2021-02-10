from a2ml.api.roi.lexer import AstError, Token

class ParserError(AstError):
    pass

class BaseNode:
    def __init__(self, token):
        self.token = token

    def position(self):
        return self.token.position

class NoOpNode(BaseNode):
    def __str__(self):
        return ""

class ConstNode(BaseNode):
    def __init__(self, token):
        super().__init__(token)
        self.value = token.value

    def __str__(self):
        if isinstance(self.value, str):
            return '"' + str(self.value) + '"'
        else:
            return str(self.value)

class VarNode(BaseNode):
    def __init__(self, token):
        super().__init__(token)
        self.name = token.value

    def __str__(self):
        return str(self.name)

class BinaryOpNode(BaseNode):
    def __init__(self, left, token, right):
        super().__init__(token)
        self.left = left
        self.op = token.type
        self.right = right

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

class UnaryOpNode(BaseNode):
    def __init__(self, token, node):
        super().__init__(token)
        self.op = token.type
        self.node = node

    def __str__(self):
        return f"({self.op} {self.node})"

class FuncNode(BaseNode):
    def __init__(self, token, arg_nodes):
        super().__init__(token)
        self.func_name = token.value
        self.arg_nodes = arg_nodes

    def __str__(self):
        return str(self.func_name) + "(" + ", ".join(map(str, self.arg_nodes)) + ")"

class Parser:
    CONSTANTS = set([Token.CONST, Token.STR_CONST, Token.INT_CONST, Token.FLOAT_CONST])

    COMPARE_OP_BITWISE_OR_PAIR_OPS = set(
        [
            Token.EQ,
            Token.EQ2,
            Token.NE,
            Token.LTE,
            Token.LT,
            Token.GTE,
            Token.GT,
            Token.NOT,
            Token.IN
        ]
    )

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.next_token()

    def error(self, msg=None):
        if self.current_token.type == Token.EOF:
            raise ParserError(f"unexpected end of expression at position {self.current_token.position}")
        else:
            msg = msg or "invalid token"
            value = self.current_token.value
            pos = self.current_token.position
            raise ParserError(f"{msg} '{value}' at position {pos}")

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.prev_token = self.current_token
            self.current_token = self.lexer.next_token()
        else:
            self.error()

    def parse(self):
        root = self.disjunction()

        if self.current_token.type != Token.EOF:
            self.error()

        return root

    def disjunction(self):
        left = self.conjunction()

        while self.current_token.type == Token.OR:
            self.eat(Token.OR)
            left = BinaryOpNode(left, self.prev_token, self.conjunction())

        return left

    def conjunction(self):
        left = self.inversion()

        while self.current_token.type == Token.AND:
            self.eat(Token.AND)
            left = BinaryOpNode(left, self.prev_token, self.inversion())

        return left

    def inversion(self):
        if self.current_token.type == Token.NOT:
            self.eat(Token.NOT)
            return UnaryOpNode(self.prev_token, self.inversion())
        else:
            return self.comparison()

    def comparison(self):
        left = self.bitwise_or()

        if self.current_token.type in Parser.COMPARE_OP_BITWISE_OR_PAIR_OPS:
            left = self.compare_op_bitwise_or_pair(left)

        return left

    def compare_op_bitwise_or_pair(self, left):
        if self.current_token.type in (Token.EQ, Token.EQ2):
            return self.eq_bitwise_or(left)
        elif self.current_token.type == Token.NE:
            return self.noteq_bitwise_or(left)
        elif self.current_token.type == Token.LTE:
            return self.lte_bitwise_or(left)
        elif self.current_token.type == Token.LT:
            return self.lt_bitwise_or(left)
        elif self.current_token.type == Token.GTE:
            return self.gte_bitwise_or(left)
        elif self.current_token.type == Token.GT:
            return self.gt_bitwise_or(left)
        elif self.current_token.type == Token.NOT:
            return self.notin_bitwise_or(left)
        if self.current_token.type == Token.IN:
            return self.in_bitwise_or(left)
        else:
            raise self.error("unknown op")

    def eq_bitwise_or(self, left):
        self.eat(Token.EQ2)
        return BinaryOpNode(left, self.prev_token, self.bitwise_or())

    def noteq_bitwise_or(self, left):
        self.eat(Token.NE)
        return BinaryOpNode(left, self.prev_token, self.bitwise_or())

    def lte_bitwise_or(self, left):
        self.eat(Token.LTE)
        return BinaryOpNode(left, self.prev_token, self.bitwise_or())

    def lt_bitwise_or(self, left):
        self.eat(Token.LT)
        return BinaryOpNode(left, self.prev_token, self.bitwise_or())

    def gte_bitwise_or(self, left):
        self.eat(Token.GTE)
        return BinaryOpNode(left, self.prev_token, self.bitwise_or())

    def gt_bitwise_or(self, left):
        self.eat(Token.GT)
        return BinaryOpNode(left, self.prev_token, self.bitwise_or())

    def notin_bitwise_or(self, left):
        self.eat(Token.NOT)
        return UnaryOpNode(self.prev_token, self.in_bitwise_or(left))

    def in_bitwise_or(self, left):
        self.eat(Token.IN)
        return UnaryOpNode(self.prev_token, self.bitwise_or())

    def bitwise_or(self):
        left = self.bitwise_xor()

        while self.current_token.type == Token.BIT_OR:
            self.eat(Token.BIT_OR)
            left = BinaryOpNode(left, self.prev_token, self.bitwise_xor())

        return left

    def bitwise_xor(self):
        left = self.bitwise_and()

        while self.current_token.type == Token.BIT_XOR:
            self.eat(Token.BIT_XOR)
            left = BinaryOpNode(left, self.prev_token, self.bitwise_and())

        return left

    def bitwise_and(self):
        left = self.shift_expr()

        while self.current_token.type == Token.BIT_AND:
            self.eat(Token.BIT_AND)
            left = BinaryOpNode(left, self.prev_token, self.shift_expr())

        return left

    def shift_expr(self):
        left = self.sum()

        while self.current_token.type in (Token.BIT_LSHIFT, Token.BIT_RSHIFT):
            self.eat(self.current_token.type)
            left = BinaryOpNode(left, self.prev_token, self.sum())

        return left

    def sum(self):
        left = self.term()

        while self.current_token.type in (Token.PLUS, Token.MINUS):
            self.eat(self.current_token.type)
            left = BinaryOpNode(left, self.prev_token, self.term())

        return left

    def term(self):
        left = self.factor()

        while self.current_token.type in (Token.MUL, Token.DIV, Token.INT_DIV, Token.MODULO):
            self.eat(self.current_token.type)
            left = BinaryOpNode(left, self.prev_token, self.factor())

        return left

    def factor(self):
        if self.current_token.type in (Token.PLUS, Token.MINUS, Token.BIT_NOT):
            self.eat(self.current_token.type)
            return UnaryOpNode(self.prev_token, self.factor())
        else:
            return self.power()

    def power(self):
        base = self.primary()

        if self.current_token.type == Token.POWER:
            self.eat(Token.POWER)
            base = BinaryOpNode(base, self.prev_token, self.factor())

        return base

    def expression(self):
        return self.disjunction()

    def primary(self):
        if self.current_token.type == Token.LPAREN:
            self.eat(Token.LPAREN)
            expr = self.expression()
            self.eat(Token.RPAREN)
            return expr
        else:
            return self.atom()

    def atom(self):
        if self.current_token.type == Token.ID:
            self.eat(Token.ID)
            if self.current_token.type == Token.LPAREN:
                return self.func_call_statement()
            else:
                return VarNode(self.prev_token)
        elif self.current_token.type in Parser.CONSTANTS:
            token = self.current_token
            self.eat(self.current_token.type)
            return ConstNode(token)
        else:
            self.error("unknown atom")

    def func_call_statement(self):
        name_token = self.prev_token
        self.eat(Token.LPAREN)

        arg_nodes = []

        if self.current_token.type != Token.RPAREN:
            arg_nodes.append(self.expression())

            while self.current_token.type == Token.COMMA:
                self.eat(Token.COMMA)
                arg_nodes.append(self.expression())

        self.eat(Token.RPAREN)

        return FuncNode(name_token, arg_nodes)
