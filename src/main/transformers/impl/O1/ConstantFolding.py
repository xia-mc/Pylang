import ast
from ast import Constant

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class ConstantFolding(ITransformer):
    def __init__(self):
        super().__init__("ConstantFolding", OptimizeLevel.O1)

    def visit_If(self, node):
        self.generic_visit(node)

        if isinstance(node.test, Constant):
            node.test = Constant(bool(node.test.value))
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)

        if (isinstance(node.left, Constant)
                and len(node.ops) == 1
                and len(node.comparators) == 1 and isinstance(node.comparators[0], Constant)):
            left = node.left.value
            # noinspection PyUnresolvedReferences
            right = node.comparators[0].value

            match type(node.ops[0]):
                case ast.Eq:
                    self.done()
                    return Constant(left == right)
                case ast.NotEq:
                    self.done()
                    return Constant(left != right)
                case ast.Lt:
                    self.done()
                    return Constant(left < right)
                case ast.LtE:
                    self.done()
                    return Constant(left <= right)
                case ast.Gt:
                    self.done()
                    return Constant(left > right)
                case ast.GtE:
                    self.done()
                    return Constant(left >= right)
                case ast.Is:
                    self.done()
                    return Constant(left is right)
                case ast.IsNot:
                    self.done()
                    return Constant(left is not right)
                case ast.In:
                    self.done()
                    return Constant(left in right)
                case ast.NotIn:
                    self.done()
                    return Constant(left not in right)

        return node

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
