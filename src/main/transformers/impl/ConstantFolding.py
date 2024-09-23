import ast
from ast import Constant

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class ConstantFolding(ITransformer):
    def __init__(self):
        super().__init__("ConstantFolding", OptimizeLevel.O1)

    def visit_BinOp(self, node):
        if isinstance(node.left, Constant) and isinstance(node.right, Constant):
            if isinstance(node.op, ast.Add):
                self.done()
                return Constant(node.left.value + node.right.value)
            elif isinstance(node.op, ast.Sub):
                self.done()
                return Constant(node.left.value - node.right.value)
            elif isinstance(node.op, ast.Mult):
                self.done()
                return Constant(node.left.value * node.right.value)
            elif isinstance(node.op, ast.Div):
                self.done()
                return Constant(node.left.value / node.right.value)

        return node
