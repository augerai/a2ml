# Lexical Grammar:
#
# NUMBER         → DIGIT+ ( "." DIGIT+ )? ;
# STRING         → "\"" <any char except "\"">* "\"" ;
# IDENTIFIER     → (ALPHA | "@") ( ALPHA | DIGIT )* ;
# ALPHA          → "a" ... "z" | "A" ... "Z" | "_" ;
# DIGIT          → "0" ... "9" ;

class AstError(Exception):
    def __init__(self, msg, position=None):
        self.position = position
        super().__init__(msg)

class LexerError(AstError):
    pass

class Token:
    EQ = "="
    EQ2 = "=="
    GT = ">"
    LT = "<"
    NE = "!="
    GTE = ">="
    LTE = "<="

    PLUS = "+"
    MINUS = "-"
    MUL = "*"
    POWER = "**"
    DIV = "/"
    INT_DIV = "//"
    MODULO = "%"

    LPAREN = "("
    RPAREN = ")"
    BIT_OR = "|"
    BIT_XOR = "^"
    BIT_AND = "&"
    BIT_NOT = "~"
    BIT_LSHIFT = "<<"
    BIT_RSHIFT = ">>"

    EXCLAMATION = "!"
    SEMI = ";"
    DOT = "."
    AT = "@"
    UNDER = "_"
    LCURCLY = "{"
    RCURCLY = "}"
    COLON = ":"
    ASSIGN = ":="
    COMMA = ","
    DQUOTE = '"'
    DOLLAR = "$"

    INT_CONST = "INT_CONST"
    FLOAT_CONST = "FLOAT_CONST"
    STR_CONST = "STR_CONST"
    CONST = "CONST"
    ID = "ID"
    AND = "and"
    OR = "or"
    NOT = "not"
    IN = "in"

    EOF = "EOF"

    COMPARISON_SYMBOLS = set([LT, EQ, GT, EXCLAMATION])
    KEYWORDS = set([AND, OR, NOT, IN])

    SYMBOLS = set(
        [SEMI, DOT, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, COMMA, BIT_OR, BIT_AND, BIT_XOR, BIT_NOT, MODULO]
    )

    CONSTANTS = {
        "None": None,
        "True": True,
        "False": False,
    }
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
        return c and (c.isalpha() or c == Token.UNDER or c == Token.AT)

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
        while self.current_char != Token.RCURCLY:
            self.advance()

        self.advance()

    def number_token(self):
        token = ''

        while self.current_char.isdigit():
            token += self.current_char
            self.advance()

        if self.current_char == Token.DOT:
            token += Token.DOT
            self.advance()

            while self.current_char.isdigit():
                token += self.current_char
                self.advance()

            return Token(float(token), Token.FLOAT_CONST)
        else:
            return Token(int(token), Token.INT_CONST)

    def name_token(self, prefix=None):
        token = (prefix or '') + self.current_char
        self.advance()

        while Lexer.is_name_part(self.current_char):
            token += self.current_char
            self.advance()

        if token in Token.KEYWORDS:
            return Token(token)
        elif token in Token.CONSTANTS:
            return Token(Token.CONSTANTS[token], Token.CONST)
        else:
            return Token(token, Token.ID)

    def string_literal(self):
        token = ''
        self.advance()

        while self.current_char != Token.DQUOTE:
            token += self.current_char
            self.advance()

        self.advance()

        return Token(token, Token.STR_CONST)

    def dollar_literal(self):
        self.advance()

        if self.current_char.isdigit():
            return self.number_token()
        else:
            return self.name_token(Token.DOLLAR)

    def colon_op(self):
        self.advance()

        if self.current_char == Token.EQ:
            self.advance()
            return Token(Token.ASSIGN)

        return Token(Token.COLON)

    def comparison_op(self):
        token = ''

        while self.current_char in Token.COMPARISON_SYMBOLS:
            token += self.current_char
            self.advance()

        # Temporary treat "="" as an "=="
        if token == Token.EQ:
            token = Token.EQ2

        return Token(token)

    def div_op(self):
        self.advance()

        if self.current_char == Token.DIV:
            self.advance()
            return Token(Token.INT_DIV)
        else:
            return Token(Token.DIV)

    def mul_or_power_op(self):
        self.advance()

        if self.current_char == Token.MUL:
            self.advance()
            return Token(Token.POWER)
        else:
            return Token(Token.MUL)

    def symbol(self):
        sym = self.current_char
        self.advance()
        return Token(sym)

    def next_token(self):
        self.skip_whitespaces()

        while self.current_char:
            if self.current_char == Token.LCURCLY:
                self.skip_comment()
                self.skip_whitespaces()
                continue

            if self.current_char.isdigit():
                return self.number_token()

            if Lexer.is_name_start(self.current_char):
                return self.name_token()

            if self.current_char == Token.DQUOTE:
                return self.string_literal()

            if self.current_char == Token.DOLLAR:
                return self.dollar_literal()

            if self.current_char == Token.COLON:
                return self.colon_op()

            if self.current_char in Token.COMPARISON_SYMBOLS:
                return self.comparison_op()

            if self.current_char == Token.DIV:
                return self.div_op()

            if self.current_char == Token.MUL:
                return self.mul_or_power_op()

            if self.current_char in Token.SYMBOLS:
                return self.symbol()

            raise LexerError(f"unexpected char: '{self.current_char}' code={ord(self.current_char)} pos=#{self.pos}")

        return Token(Token.EOF)

    def all_tokens(self):
        res = []
        token = self.next_token()

        while token.type != Token.EOF:
            res.append(token)
            token = self.next_token()

        return res
