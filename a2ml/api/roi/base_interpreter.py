import random
from inspect import getfullargspec


class BaseInterpreter(object):
    MAX_ARGS_COUNT = 255

    def snake_case(self, str):
        res = ''

        for i, c in enumerate(str):
            if c.isupper() and i > 0:
                res += "_"

            res += c.lower()

        return res

    def node_method_name(self, node):
        return 'evaluate_' + self.snake_case(type(node).__name__)

    def evaluate(self, node):
        evaluateor = getattr(self, self.node_method_name(node), self.generic_evaluate)
        return evaluateor(node)

    def generic_evaluate(self, node):
        raise Exception('No {} method'.format(self.node_method_name(node)))

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
            "if": BaseInterpreter.logic_if,
            "@if": BaseInterpreter.logic_if,

            # Math
            "abs": BaseInterpreter.abs,
            "min": BaseInterpreter.min,
            "max": BaseInterpreter.max,
            "round": BaseInterpreter.round,
            "randint": BaseInterpreter.randint,
            "random": BaseInterpreter.random,

            # Str
            "len": BaseInterpreter.len,
        }

    @staticmethod
    def known_funcs():
        res = {}
        funcs = BaseInterpreter.func_values()

        for func_name, func in funcs.items():
            spec = getfullargspec(func)

            # -1 for interpreter it self
            # -len(spec.defaults) for default arg values
            min_count = len(spec.args) - 1 - len(spec.defaults or [])
            max_count = len(spec.args) - 1

            if spec.varargs:
                max_count = BaseInterpreter.MAX_ARGS_COUNT

            res[func_name] = range(min_count, max_count + 1)

        return res
