import ast
from ast import Constant
from typing import Optional, Any

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class ConstantFolding(ITransformer):
    def __init__(self):
        super().__init__("ConstantFolding", OptimizeLevel.O1)

    def visit_If(self, node):
        if isinstance(node.test, Constant) and not isinstance(node.test.value, bool):
            self.done()
            node.test = Constant(bool(node.test.value))
        return self.generic_visit(node)

    def visit_While(self, node):
        if isinstance(node.test, Constant) and not isinstance(node.test.value, bool):
            self.done()
            node.test = Constant(bool(node.test.value))
        return self.generic_visit(node)

    def visit_Compare(self, node):
        if (isinstance(node.left, Constant)
                and len(node.ops) == 1
                and len(node.comparators) == 1 and isinstance(node.comparators[0], Constant)):
            left = node.left.value
            right = node.comparators[0].value

            result: Optional[bool] = None
            try:
                match type(node.ops[0]):
                    case ast.Eq:
                        result = left == right
                    case ast.NotEq:
                        result = left != right
                    case ast.Lt:
                        result = left < right
                    case ast.LtE:
                        result = left <= right
                    case ast.Gt:
                        result = left > right
                    case ast.GtE:
                        result = left >= right
                    case ast.Is:
                        result = left is right
                    case ast.IsNot:
                        result = left is not right
                    case ast.In:
                        result = left in right
                    case ast.NotIn:
                        result = left not in right
            except Exception as e:
                self.flag(e, node)
                result = None

            if result is not None:
                self.done()
                return Constant(value=result)

        return self.generic_visit(node)

    def visit_BinOp(self, node):
        if isinstance(node.left, Constant) and isinstance(node.right, Constant):
            left = node.left.value
            right = node.right.value

            result: Optional[Any] = None
            try:
                match type(node.op):
                    case ast.Add:
                        result = left + right
                    case ast.BitAnd:
                        result = left & right
                    case ast.BitOr:
                        result = left | right
                    case ast.BitXor:
                        result = left ^ right
                    case ast.Div:
                        result = left / right
                    case ast.FloorDiv:
                        result = left // right
                    case ast.LShift:
                        result = left << right
                    case ast.MatMult:
                        result = left @ right
                    case ast.Mod:
                        result = left % right
                    case ast.Mult:
                        result = left * right
                    case ast.Pow:
                        result = left ** right
                    case ast.RShift:
                        result = left >> right
                    case ast.Sub:
                        result = left - right
            except Exception as e:
                self.flag(e, node)
                result = None

            if result is not None:
                self.done()
                return Constant(value=result)

        return self.generic_visit(node)
