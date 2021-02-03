from a2ml.api.roi.lexer import AstError
from a2ml.api.roi.node_visitor import NodeVisitor

class ValidationError(AstError):
    pass

class Validator(NodeVisitor):
    def __init__(self, root, known_vars, known_funcs):
        super().__init__(root)
        self.known_vars = known_vars
        self.known_funcs = known_funcs

    def validate(self):
        return self.evaluate(self.root)

    def evaluate_no_op_node(self, node):
        return True

    def evaluate_const_node(self, node):
        return True

    def evaluate_var_node(self, node):
        if node.name in self.known_vars:
            return True
        else:
            raise ValidationError(f"unknown variable '{node.name}' at position {node.position}")

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
                counts = list(map(str, self.known_funcs[node.func_name]))

                if len(counts) > 1:
                    counts = counts[0:-2] + [counts[-2] + " or " + counts[-1]]

                expected = ", ".join(counts)

                raise ValidationError(
                    f"invalid arguments count on '{node.func_name}' function, expected {expected} got {args_count} at position {node.position}"
                )
        else:
            raise ValidationError(f"unknown function '{node.func_name}' at position {node.position}")

