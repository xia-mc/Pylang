import ast
from ast import Constant

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class ConstantFolding(ITransformer):
    def __init__(self):
        super().__init__("ConstantFolding", OptimizeLevel.O1)

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.left, Constant) and isinstance(node.right, Constant):
            left = node.left.value
            right = node.right.value
            match type(node.op):
                case ast.Add:
                    self.done()
                    return Constant(left + right)
                case ast.BitAnd:
                    self.done()
                    return Constant(left & right)
                case ast.BitOr:
                    self.done()
                    return Constant(left | right)
                case ast.BitXor:
                    self.done()
                    return Constant(left ^ right)
                case ast.Div:
                    self.done()
                    return Constant(left / right)
                case ast.FloorDiv:
                    self.done()
                    return Constant(left // right)
                case ast.LShift:
                    self.done()
                    return Constant(left << right)
                case ast.MatMult:
                    self.done()
                    return Constant(left @ right)
                case ast.Mod:
                    self.done()
                    return Constant(left % right)
                case ast.Mult:
                    self.done()
                    return Constant(left * right)
                case ast.Pow:
                    self.done()
                    return Constant(left ** right)
                case ast.RShift:
                    self.done()
                    return Constant(left >> right)
                case ast.Sub:
                    self.done()
                    return Constant(left - right)

        return node
