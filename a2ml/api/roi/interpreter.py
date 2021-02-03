from inspect import getfullargspec

from a2ml.api.roi.lexer import *
from a2ml.api.roi.node_visitor import NodeVisitor
from a2ml.api.roi.validator import Validator

class InterpreterError(AstError):
    pass

class Interpreter(NodeVisitor):
    MAX_ARGS_COUNT = 255

    def __init__(self, root, variables):
        super().__init__(root)
        self.variables = variables

    def run(self):
        Validator(self.root, self.variables, self.known_funcs()).validate()
        return self.evaluate(self.root)

    # Builtin functions

    def min(self, arg1, arg2, *args):
        return min(arg1, arg2, *args)

    def max(self, arg1, arg2, *args):
        return max(arg1, arg2, *args)

    def logic_if(self, predicate, true_value, false_value):
        if self.evaluate(predicate):
            return self.evaluate(true_value)
        else:
            return self.evaluate(false_value)

    def func_values(self):
        return {
            # Math
            "min": self.min,
            "max": self.max,
            "if": self.logic_if,
        }

    def known_funcs(self):
        res = {}
        funcs = self.func_values()

        for func_name, func in funcs.items():
            spec = getfullargspec(func)
            min_count = len(spec.args) - 1

            if spec.varargs:
                args_count = range(min_count, self.MAX_ARGS_COUNT + 1)
            else:
                args_count = [min_count]

            res[func_name] = args_count

        return res

    def evaluate_no_op_node(self, node):
        pass

    def evaluate_const_node(self, node):
        return node.value

    def evaluate_var_node(self, node):
        return self.variables[node.name]

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
            return func(*node.arg_nodes)
        else:
            args = list(map(lambda node: self.evaluate(node), node.arg_nodes))
            return func(*args)

    def error(self, msg):
        raise InterpreterError(msg)
