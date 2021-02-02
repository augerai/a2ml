EQ = "="
GT = ">"
LT = "<"
EXCLAMATION = "!"
SEMI = ";"
DOT = "."
PLUS = "+"
MINUS = "-"
MUL = "*"
POWER = "**"
DIV = "/"
INT_DIV = "//"
LPAREN = "("
RPAREN = ")"
PIPE = "|"
CARET = "^"
AMPERSAND = "&"
TILDE = "~"
PERCENT = "%"

AT = "@"
UNDER = "_"
LCURCLY = "{"
RCURCLY = "}"
COLON = ":"
ASSIGN = ":="
COMMA = ","
DQUOTE = '"'
DOLLAR = "$"

INT_CONST = 'INT_CONST'
FLOAT_CONST = 'FLOAT_CONST'
ID = "ID"
STRING = "STRING"
AND = "and"
OR = "or"
NOT = "not"

COMPARISON_SYMBOLS = set([LT, EQ, GT, EXCLAMATION])
KEYWORDS = set([AND, OR, NOT])

SYMBOLS = set(
    [SEMI, DOT, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, COMMA, PIPE, AMPERSAND, CARET, TILDE, PERCENT]
)

class AstError(Exception):
    def __init__(self, msg, position=None):
        self.position = position
        super().__init__(msg)

class LexerError(AstError):
    pass

class Token:
    def __init__(self, value, type=None):
        self.value = value
        self.type = type or value

    def __str__(self):
        return f"{self.type} -> {self.value}"

class Lexer:
    def __init__(self, str):
        self.str = str
        self.pos = 0
        self.advance()

    @staticmethod
    def is_name_start(c):
        return c and (c.isalnum() or c == UNDER or c == AT)

    @staticmethod
    def is_name_part(c):
        return Lexer.is_name_start(c) or c.isdigit()

    def advance(self):
        if self.pos < len(self.str):
            self.current_char = self.str[self.pos]
            self.pos += 1
        else:
            self.current_char = ''

        return self.current_char

    def is_whitespace(self, c):
        if c:
            return c.isspace()

    def skip_whitespaces(self):
        while self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        while self.current_char != RCURCLY:
            self.advance()

        self.advance()

    def number_token(self):
        token = ''

        while self.current_char.isdigit():
            token += self.current_char
            self.advance()

        if self.current_char == DOT:
            token += DOT
            self.advance()

            while self.current_char.isdigit():
                token += current_char
                self.advance()

            return Token(float(token), FLOAT_CONST)
        else:
            return Token(int(token), INT_CONST)

    def name_token(self):
        token = self.current_char
        self.advance()

        while Lexer.is_name_part(self.current_char):
            token += self.current_char
            self.advance()

        if token in KEYWORDS:
            return Token(token)
        else:
            return Token(token, ID)

    def string_literal(self):
        token = ''
        self.advance()

        while self.current_char != DQUOTE:
            token += self.current_char
            self.advance()

        self.advance()

        return Token(token, STRING)

    def dollar_literal(self):
        self.advance()

        if self.current_char.isdigit():
            return self.number_token()
        else:
            return self.name_token()

    def colon_op(self):
        self.advance()

        if self.current_char == EQ:
            self.advance()
            return Token(ASSIGN)

        return Token(COLON)

    def comparison_op(self):
        token = ''

        while self.current_char in COMPARISON_SYMBOLS:
            token += self.current_char
            self.advance()

        return Token(token)

    def div_op(self):
        self.advance()

        if self.current_char == DIV:
            self.advance()
            return Token(INT_DIV)
        else:
            return Token(DIV)

    def mul_or_power_op(self):
        self.advance()

        if self.current_char == MUL:
            self.advance()
            return Token(POWER)
        else:
            return Token(MUL)

    def symbol(self):
        sym = self.current_char
        self.advance()
        return Token(sym)

    def next_token(self):
        self.skip_whitespaces()

        while self.current_char:
            if self.current_char == LCURCLY:
                self.skip_comment()
                self.skip_whitespaces()
                continue

            if self.current_char.isdigit():
                return self.number_token()

            if Lexer.is_name_start(self.current_char):
                return self.name_token()

            if self.current_char == DQUOTE:
                return self.string_literal()

            if self.current_char == DOLLAR:
                return self.dollar_literal()

            if self.current_char == COLON:
                return self.colon_op()

            if self.current_char in COMPARISON_SYMBOLS:
                return self.comparison_op()

            if self.current_char == DIV:
                return self.div_op()

            if self.current_char == MUL:
                return self.mul_or_power_op()

            if self.current_char in SYMBOLS:
                return self.symbol()

            raise LexerError(f"unexpected char: '{self.current_char}' code={ord(self.current_char)} pos=#{self.pos}")

    def all_tokens(self):
        res = []
        token = self.next_token()

        while token:
            res.append(token.value)
            token = self.next_token()

        return res
