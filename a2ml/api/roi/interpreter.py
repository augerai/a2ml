from a2ml.api.roi.lexer import *
from a2ml.api.roi.base_interpreter import BaseInterpreter
from a2ml.api.roi.validator import Validator

class InterpreterError(AstError):
    pass

class Interpreter(BaseInterpreter):
    def __init__(self, expression, vars_mapping={}):
        self.expression = expression
        self.vars_mapping = vars_mapping

    def run(self, variables={}):
        known_vars = self.get_kwnown_vars(variables) | set(self.vars_mapping.keys())
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
    def get_kwnown_vars(self, variables):
        if isinstance(variables, list):
            res = set(variables[0])

            for vars in variables:
                res = res.intersection(set(vars.keys()))

            return res
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
        if node.func_name in ("if", "@if"):
            return func(self, *node.arg_nodes)
        else:
            args = list(map(lambda node: self.evaluate(node), node.arg_nodes))
            return func(self, *args)

    def error(self, msg):
        raise InterpreterError(msg)
