import random
from inspect import getfullargspec

from a2ml.api.roi.lexer import *
from a2ml.api.roi.node_visitor import NodeVisitor
from a2ml.api.roi.validator import Validator

class InterpreterError(AstError):
    pass

class Interpreter(NodeVisitor):
    MAX_ARGS_COUNT = 255

    def __init__(self, expression, vars_mapping={}):
        self.expression = expression
        self.vars_mapping = vars_mapping

    def run(self, variables={}):
        known_vars = self.get_kwnown_vars(variables) | set(self.vars_mapping.keys())
        validator = Validator(self.expression, known_vars, self.known_funcs())
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
    def get_kwnown_vars(self, variables):
        if isinstance(variables, list):
            res = set(variables[0])

            for vars in variables:
                res = res.intersection(set(vars.keys()))

            return res
        else:
            return set(variables.keys())

    # Builtin functions

    @staticmethod
    def abs(_, x):
        return abs(x)

    @staticmethod
    def len(_, x):
        return len(x)

    @staticmethod
    def logic_if(interpreter, predicate, true_value, false_value):
        if interpreter.evaluate(predicate):
            return interpreter.evaluate(true_value)
        else:
            return interpreter.evaluate(false_value)

    @staticmethod
    def min(_, arg1, arg2, *args):
        return min(arg1, arg2, *args)

    @staticmethod
    def max(_, arg1, arg2, *args):
        return max(arg1, arg2, *args)

    @staticmethod
    def randint(_, a, b):
        return random.randint(a, b)

    @staticmethod
    def random(_):
        return random.random()

    @staticmethod
    def round(_, x, ndigits=None):
        return round(x, ndigits)

    @staticmethod
    def func_values():
        return {
            # Logic
            "if": Interpreter.logic_if,

            # Math
            "abs": Interpreter.abs,
            "min": Interpreter.min,
            "max": Interpreter.max,
            "round": Interpreter.round,
            "randint": Interpreter.randint,
            "random": Interpreter.random,

            # Str
            "len": Interpreter.len,
        }

    @staticmethod
    def known_funcs():
        res = {}
        funcs = Interpreter.func_values()

        for func_name, func in funcs.items():
            spec = getfullargspec(func)

            # -1 for interpreter it self
            # -len(spec.defaults) for default arg values
            min_count = len(spec.args) - 1 - len(spec.defaults or [])
            max_count = len(spec.args) - 1

            if spec.varargs:
                max_count = Interpreter.MAX_ARGS_COUNT

            res[func_name] = range(min_count, max_count + 1)

        return res

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

        if node.op == MUL:
            return left * right
        elif node.op == DIV:
            return left / right
        elif node.op == INT_DIV:
            return left // right
        elif node.op == MODULO:
            return left % right
        elif node.op == PLUS:
            return left + right
        elif node.op == MINUS:
            return left - right
        elif node.op == POWER:
            return left ** right
        elif node.op == GT:
            return left > right
        elif node.op == GTE:
            return left >= right
        elif node.op == LT:
            return left < right
        elif node.op == LTE:
            return left <= right
        elif node.op == EQ2 or node.op == EQ:
            return left == right
        elif node.op == NE:
            return left != right
        elif node.op == BIT_XOR:
            return left ^ right
        elif node.op == BIT_OR:
            return left | right
        elif node.op == BIT_AND:
            return left & right
        elif node.op == BIT_LSHIFT:
            return left << right
        elif node.op == BIT_RSHIFT:
            return left >> right
        elif node.op == IN:
            return left in right
        elif node.op == OR:
            return left or right
        elif node.op == AND:
            return left and right
        else:
            raise self.error(f"unknown binary operator '{node.op}'")

    def evaluate_unary_op_node(self, node):
        value = self.evaluate(node.node)

        if node.op == PLUS:
            return value
        elif node.op == MINUS:
            return -value
        elif node.op == BIT_NOT:
            return ~value
        elif node.op == NOT:
            return not value
        else:
            raise self.error(f"unknown unary operator '{node.op}'")

    def evaluate_func_node(self, node):
        func = self.func_values()[node.func_name]
        if node.func_name == "if":
            return func(self, *node.arg_nodes)
        else:
            args = list(map(lambda node: self.evaluate(node), node.arg_nodes))
            return func(self, *args)

    def error(self, msg):
        raise InterpreterError(msg)
