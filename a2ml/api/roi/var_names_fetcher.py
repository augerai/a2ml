from .base_interpreter import BaseInterpreter
from .lexer import AstError, Lexer
from .parser import Parser, TopNode

class VarNamesFetcher(BaseInterpreter):
    def __init__(self, expression):
        self.expression = expression

    def fetch(self):
        parser = Parser(Lexer(self.expression))
        root = parser.parse()

        self.var_names = set()
        self.evaluate(root)
        return list(self.var_names)

    def evaluate_no_op_node(self, node):
        pass

    def evaluate_const_node(self, node):
        pass

    def evaluate_var_node(self, node):
        self.var_names.add(node.name)

    def evaluate_var_def_node(self, node):
        pass

    def evaluate_binary_op_node(self, node):
        self.evaluate(node.left)
        self.evaluate(node.right)

    def evaluate_unary_op_node(self, node):
        self.evaluate(node.node)

    def evaluate_func_node(self, node):
        list(map(lambda node: self.evaluate(node), node.arg_nodes))

    def evaluate_tuple_node(self, node):
        list(map(lambda node: self.evaluate(node), node.item_nodes))

    def evaluate_top_node(self, node):
        list(map(lambda n: self.evaluate(n), node.child_nodes()))

    def evaluate_with_node(self, node):
        list(map(lambda n: self.evaluate(n), node.with_item_nodes))

    def evaluate_with_item_node(self, node):
        nodes = [node.source_node]

        if node.alias_node:
            nodes.append(node.alias_node)

        list(map(lambda n: self.evaluate(n), nodes))
