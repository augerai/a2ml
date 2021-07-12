import json
import numpy as np

from operator import attrgetter
from itertools import groupby

from .base_interpreter import BaseInterpreter
from .lexer import AstError, Token
from .validator import Validator

class InterpreterError(AstError):
    pass

class MissedVariable(InterpreterError):
    pass

class TopRecord:
    def __init__(self, row, group_key, order_value):
        self.row = row
        self.group_key = group_key
        self.order_value = order_value

class Interpreter(BaseInterpreter):
    def __init__(self, expression, vars_mapping={}):
        self.expression = expression
        self.vars_mapping = vars_mapping

    def run(self, variables={}, filter=False):
        known_vars = self.get_known_vars(variables) | set(self.vars_mapping.keys())
        validator = Validator(self.expression, known_vars)
        validation_result = validator.validate(force_raise=True)
        self.root = validation_result.tree

        if isinstance(variables, list):
            return self.evaluate_for_list(self.root, variables, filter=filter)
        else:
            self.variables = variables
            return self.evaluate(self.root)

    def evaluate_for_list(self, node, rows, filter=False):
        # top expressions requires aggregation
        if node.require_aggregation:
            return self.evaluate(node, rows)
        else:
            res = []

            for vars in rows:
                self.variables = vars
                value = self.evaluate(node)
                if filter:
                    if value:
                        res.append(vars)
                else:
                    res.append(value)

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
        left = lambda: self.evaluate(node.left)
        right = lambda: self.evaluate(node.right)

        if node.op == Token.MUL:
            return left() * right()
        elif node.op == Token.DIV:
            return left() / right()
        elif node.op == Token.INT_DIV:
            return left() // right()
        elif node.op == Token.MODULO:
            return left() % right()
        elif node.op == Token.PLUS:
            return left() + right()
        elif node.op == Token.MINUS:
            return left() - right()
        elif node.op == Token.POWER:
            return left() ** right()
        elif node.op == Token.GT:
            return left() > right()
        elif node.op == Token.GTE:
            return left() >= right()
        elif node.op == Token.LT:
            return left() < right()
        elif node.op == Token.LTE:
            return left() <= right()
        elif node.op == Token.EQ2 or node.op == Token.EQ:
            return left() == right()
        elif node.op == Token.NE:
            return left() != right()
        elif node.op == Token.BIT_XOR:
            return left() ^ right()
        elif node.op == Token.BIT_OR:
            return left() | right()
        elif node.op == Token.BIT_AND:
            return left() & right()
        elif node.op == Token.BIT_LSHIFT:
            return left() << right()
        elif node.op == Token.BIT_RSHIFT:
            return left() >> right()
        elif node.op == Token.IN:
            return left() in right()
        elif node.op == Token.OR:
            return left() or right()
        elif node.op == Token.AND:
            return left() and right()
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

    def evaluate_func_node(self, node, rows=None):
        func = self.func_values()[node.func_name]

        if Interpreter.is_static_func(func):
            func_args = [self]
        else:
            func_args = []

        if node.func_name in ("if", "@if"):
            func_args += node.arg_nodes
        elif rows:
            func_args += list(map(lambda n: self.evaluate_for_list(n, rows), node.arg_nodes))
        else:
            func_args += list(map(lambda n: self.evaluate(n), node.arg_nodes))

        return func(*func_args)

    def evaluate_tuple_node(self, node):
        return tuple(map(lambda n: self.evaluate(n), node.item_nodes))

    def evaluate_top_node(self, node, rows):
        if node.nested_node:
            rows = self.evaluate(node.nested_node, rows)

        if node.where_node:
            rows = self.evaluate_for_list(node.where_node, rows, filter=True)

        if node.group_node:
            group_keys = self.evaluate_for_list(node.group_node, rows)
        else:
            group_keys = np.zeros(len(rows))

        if node.order_node:
            order_values = self.evaluate_for_list(node.order_node, rows)
        else:
            order_values = np.arange(len(rows))

        table = [TopRecord(row, group_keys[i], order_values[i]) for i, row in enumerate(rows)]
        table.sort(key=attrgetter('group_key'))

        if node.limit_node:
            limit = self.evaluate(node.limit_node)
        else:
            limit = np.inf

        result = []

        for key, records in groupby(table, attrgetter('group_key')):
            records = list(records)

            if node.with_node:
                for with_item_node in node.with_node.with_item_nodes:
                    col_value = self.evaluate(with_item_node.source_node, [item.row for item in records])
                    col_name = with_item_node.alias()

                    for item in records:
                        item.row[col_name] = col_value

            if node.having_node:
                # Drop whole group if none of the rows meet having expression
                having = self.evaluate_for_list(node.having_node, [item.row for item in records])
                if not any(having):
                    records = []

            records.sort(reverse=node.kind == Token.TOP, key=attrgetter('order_value'))
            for ri in range(min(len(records), limit)):
                result.append(records[ri])

        result.sort(key=attrgetter('order_value'), reverse=node.kind == Token.TOP)
        return [item.row for item in result]

    def error(self, msg):
        raise InterpreterError(msg)
