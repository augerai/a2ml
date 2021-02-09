from a2ml.api.roi.base_interpreter import BaseInterpreter
from a2ml.api.roi.lexer import AstError, Token
from a2ml.api.roi.validator import Validator

class InterpreterError(AstError):
    pass

class Interpreter(BaseInterpreter):
    def __init__(self, expression, vars_mapping={}):
        self.expression = expression
        self.vars_mapping = vars_mapping

    def run(self, variables={}):
        known_vars = self.get_known_vars(variables) | set(self.vars_mapping.keys())
        validator = Validator(self.expression, known_vars)
        validation_result = validator.validate(force_raise=True)
        self.root = validation_result.tree

        if isinstance(variables, list):
            res = []

            for vars in variables:
                self.variables = vars
                res.append(self.evaluate(self.root))

            return res
        else:
            self.variables = variables
            return self.evaluate(self.root)

    '''
    Extract names from variable list
    if variables is a dict just return all keys
    if variables is a list of dicts extract keys from each line and return their intersection
    '''
    def get_known_vars(self, variables):
        if isinstance(variables, list):
            if len(variables) > 0:
                res = set(variables[0])

                for vars in variables:
                    res = res.intersection(set(vars.keys()))

                return res
            else:
                return set()
        else:
            return set(variables.keys())

    def evaluate_no_op_node(self, node):
        pass

    def evaluate_const_node(self, node):
        return node.value

    def evaluate_var_node(self, node):
        var_name = self.vars_mapping.get(node.name, node.name)
        return self.variables[var_name]

    def evaluate_binary_op_node(self, node):
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)

        if node.op == Token.MUL:
            return left * right
        elif node.op == Token.DIV:
            return left / right
        elif node.op == Token.INT_DIV:
            return left // right
        elif node.op == Token.MODULO:
            return left % right
        elif node.op == Token.PLUS:
            return left + right
        elif node.op == Token.MINUS:
            return left - right
        elif node.op == Token.POWER:
            return left ** right
        elif node.op == Token.GT:
            return left > right
        elif node.op == Token.GTE:
            return left >= right
        elif node.op == Token.LT:
            return left < right
        elif node.op == Token.LTE:
            return left <= right
        elif node.op == Token.EQ2 or node.op == Token.EQ:
            return left == right
        elif node.op == Token.NE:
            return left != right
        elif node.op == Token.BIT_XOR:
            return left ^ right
        elif node.op == Token.BIT_OR:
            return left | right
        elif node.op == Token.BIT_AND:
            return left & right
        elif node.op == Token.BIT_LSHIFT:
            return left << right
        elif node.op == Token.BIT_RSHIFT:
            return left >> right
        elif node.op == Token.IN:
            return left in right
        elif node.op == Token.OR:
            return left or right
        elif node.op == Token.AND:
            return left and right
        else:
            raise self.error(f"unknown binary operator '{node.op}'")

    def evaluate_unary_op_node(self, node):
        value = self.evaluate(node.node)

        if node.op == Token.PLUS:
            return value
        elif node.op == Token.MINUS:
            return -value
        elif node.op == Token.BIT_NOT:
            return ~value
        elif node.op == Token.NOT:
            return not value
        else:
            raise self.error(f"unknown unary operator '{node.op}'")

    def evaluate_func_node(self, node):
        func = self.func_values()[node.func_name]

        # breakpoint()
        if Interpreter.is_static_func(func):
            func_args = [self]
        else:
            func_args = []

        if node.func_name in ("if", "@if"):
            func_args += node.arg_nodes
        else:
            func_args += list(map(lambda n: self.evaluate(n), node.arg_nodes))

        return func(*func_args)

    def error(self, msg):
        raise InterpreterError(msg)
