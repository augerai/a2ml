class NodeVisitor(object):
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
