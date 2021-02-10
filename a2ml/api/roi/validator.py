from a2ml.api.roi.base_interpreter import BaseInterpreter
from a2ml.api.roi.lexer import AstError, Lexer
from a2ml.api.roi.parser import Parser

class ValidationError(AstError):
    pass

class ValidationResult:
    def __init__(self, is_valid=True, error=None, tree=None):
        self.is_valid = is_valid
        self.error = error
        self.tree = tree

class Validator(BaseInterpreter):
    def __init__(self, expression, known_vars):
        self.expression = expression
        self.known_vars = known_vars
        self.known_funcs = BaseInterpreter.known_funcs()
        self.root = None

    def validate(self, force_raise=True):
        try:
            parser = Parser(Lexer(self.expression))
            self.root = parser.parse()
            self.evaluate(self.root)
            return ValidationResult(is_valid=True, tree=self.root)
        except AstError as e:
            if force_raise:
                raise e
            else:
                return ValidationResult(is_valid=False, error=str(e), tree=self.root)

    def evaluate_no_op_node(self, node):
        return True

    def evaluate_const_node(self, node):
        return True

    def evaluate_var_node(self, node):
        if node.name in self.known_vars:
            return True
        else:
            raise ValidationError(f"unknown variable '{node.name}' at position {node.position()}")

    def evaluate_binary_op_node(self, node):
        return self.evaluate(node.left) and self.evaluate(node.right)

    def evaluate_unary_op_node(self, node):
        return self.evaluate(node.node)

    def evaluate_func_node(self, node):
        if node.func_name in self.known_funcs:
            args_count = len(node.arg_nodes)

            if args_count in self.known_funcs[node.func_name]:
                return all(map(lambda node: self.evaluate(node), node.arg_nodes))
            else:
                expected_args_count = self.known_funcs[node.func_name]
                if isinstance(expected_args_count, range):
                    expected = f"from {expected_args_count.start} to {expected_args_count.stop - 1}"
                else:
                    counts = list(map(str, ))

                    if len(counts) > 1:
                        counts = counts[0:-2] + [counts[-2] + " or " + counts[-1]]

                    expected = ", ".join(counts)

                raise ValidationError(
                    f"invalid arguments count on '{node.func_name}' function, expected {expected} got {args_count} at position {node.position()}"
                )
        else:
            raise ValidationError(f"unknown function '{node.func_name}' at position {node.position()}")

