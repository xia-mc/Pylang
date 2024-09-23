import ast
from ast import Constant, Call, Name, Assign, Module
from typing import Any, SupportsIndex

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class LoopUnfolding(ITransformer):
    def __init__(self):
        super().__init__("LoopUnfolding", OptimizeLevel.O2)

    def visit_For(self, node):
        self.generic_visit(node)

        if (isinstance(node.iter, Call) and isinstance(node.iter.func, Name)
                and node.iter.func.id == range.__name__):  # If they overwrite range function, then crash lol
            evalRange = self.evaluate_range(node.iter)
            if evalRange is None:
                return node

            start, end, step = evalRange
            body = list()
            for i in range(start, end, step):
                target_assignment = Assign(targets=node.target, value=Constant(value=i))
                body.append(target_assignment)
                body.extend(node.body)

            return ast.copy_location(Module(body=body), node)

        return node

    @staticmethod
    def evaluate_range(rangeExpr: Call) -> tuple[SupportsIndex, SupportsIndex, SupportsIndex] | None:
        """
        :param rangeExpr: an expr object with range function.
        :return: start, stop, step. or none means can't be evaluated.
        """
        def getOrThrow(expr) -> Any:
            if isinstance(expr, Constant):
                return expr.value
            raise RuntimeError("Expr can't be evaluated.")

        try:
            args = rangeExpr.args
            match len(args):
                case 1:
                    return 0, getOrThrow(args[0]), 1
                case 2:
                    return getOrThrow(args[0]), getOrThrow(args[1]), 1
                case 3:
                    return getOrThrow(args[0]), getOrThrow(args[1]), getOrThrow(args[2])
                case _:
                    return None
        except RuntimeError:
            return None
