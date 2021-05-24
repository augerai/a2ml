import math
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

    def evaluate(self, node, rows=None):
        evaluateor = getattr(self, self.node_method_name(node), self.generic_evaluate)

        if rows is None:
            return evaluateor(node)
        else:
            return evaluateor(node, rows)

    def generic_evaluate(self, node):
        raise Exception('No {} method'.format(self.node_method_name(node)))

    # Builtin functions

    @staticmethod
    def logic_if(interpreter, predicate, true_value, false_value):
        if interpreter.evaluate(predicate):
            return interpreter.evaluate(true_value)
        else:
            return interpreter.evaluate(false_value)

    @staticmethod
    def agg_max(_, args):
        return max(args)

    @staticmethod
    def agg_min(_, args):
        return min(args)

    @staticmethod
    def log(_, x, base=math.e):
        return math.log(x, base)

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
    def func_values():
        return {
            # Logic
            "if": BaseInterpreter.logic_if,
            "@if": BaseInterpreter.logic_if,

            # Aggregation
            "agg_max": BaseInterpreter.agg_max,
            "agg_min": BaseInterpreter.agg_min,

            # Math
            "abs": abs,
            "ceil": math.ceil,
            "cos": math.cos,
            "exp": math.exp,
            "floor": math.floor,
            "log10": math.log10,
            "log2": math.log2,
            "round": round,
            "sin": math.sin,
            "sqrt": math.sqrt,
            "tan": math.tan,

            # Str
            "len": len,

            # For these builtin functions getfullargspec doesn't work so redefine them as a staticmethods
            "log": BaseInterpreter.log,
            "max": BaseInterpreter.max,
            "min": BaseInterpreter.min,
            "randint": BaseInterpreter.randint,
            "random": BaseInterpreter.random,
        }

    @staticmethod
    def is_static_func(func):
        return func.__qualname__.startswith(f"{BaseInterpreter.__name__}.")

    @staticmethod
    def known_funcs():
        res = {}
        funcs = BaseInterpreter.func_values()

        for func_name, func in funcs.items():
            # All static functions defined in BaseInterpreter accept interpreter instance as 1 parameter
            if BaseInterpreter.is_static_func(func):
                self_arg_count = 1
            else:
                self_arg_count = 0

            spec = getfullargspec(func)

            # -1 for interpreter it self
            # -len(spec.defaults) for default arg values
            min_count = len(spec.args) - self_arg_count - len(spec.defaults or [])
            max_count = len(spec.args) - self_arg_count

            if spec.varargs:
                max_count = BaseInterpreter.MAX_ARGS_COUNT

            res[func_name] = range(min_count, max_count + 1)

        return res
