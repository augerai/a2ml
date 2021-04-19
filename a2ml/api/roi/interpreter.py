import json
import numpy as np

from operator import attrgetter
from itertools import groupby

from a2ml.api.roi.base_interpreter import BaseInterpreter
from a2ml.api.roi.lexer import AstError, Token
from a2ml.api.roi.validator import Validator

class InterpreterError(AstError):
    pass

class MissedVariable(InterpreterError):
    pass

class TopRecord:
    def __init__(self, i, group_key, order_value):
        self.i = i
        self.group_key = group_key
        self.order_value = order_value

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
            self.rows = variables
            return self.evaluate_for_list(self.root)
        else:
            self.variables = variables
            return self.evaluate(self.root)

    def evaluate_for_list(self, node):
        if node.require_aggregation:
            return self.evaluate(node)
        else:
            res = []

            for vars in self.rows:
                self.variables = vars
                res.append(self.evaluate(node))

            return res

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
        if var_name in self.variables:
            return self.variables[var_name]
        elif var_name.startswith("$") and var_name[1:] in self.variables:
            # for non-known vars try to just look up in row
            return self.variables[var_name[1:]]
        else:
            raise MissedVariable(f"missed var `{var_name}` in row `{json.dumps(self.variables)}`")


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

        if Interpreter.is_static_func(func):
            func_args = [self]
        else:
            func_args = []

        if node.func_name in ("if", "@if"):
            func_args += node.arg_nodes
        else:
            func_args += list(map(lambda n: self.evaluate(n), node.arg_nodes))

        return func(*func_args)

    def evaluate_top_node(self, node):
        # True - means row matches top expression, False - row doesn't match
        selected = np.array([True for _ in range(len(self.rows))])

        if node.nested_node:
            selected &= self.evaluate(node.nested_node)

        if node.where_node:
            selected &= self.evaluate_for_list(node.where_node)

        if node.group_node:
            group_keys = self.evaluate_for_list(node.group_node)
        else:
            group_keys = np.zeros(len(self.rows))

        order_values = self.evaluate_for_list(node.order_node)

        table = [TopRecord(i, group_keys[i], order_values[i]) for i, is_in in enumerate(selected) if is_in]
        table.sort(key=attrgetter('group_key'))

        limit = self.evaluate(node.limit_node)
        result = np.array([False for _ in range(len(self.rows))])

        for key, records in groupby(table, attrgetter('group_key')):
            records = list(records)
            records.sort(reverse=node.top, key=attrgetter('order_value'))
            for ri in range(min(len(records), limit)):
                result[records[ri].i] = True

        return result

    def error(self, msg):
        raise InterpreterError(msg)
