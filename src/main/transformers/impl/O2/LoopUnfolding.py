import ast
from ast import Constant, Call, Name, Assign, For, Module
from typing import Any, Optional, Tuple, SupportsIndex

import Const
from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class LoopUnfolding(ITransformer):
    def __init__(self):
        super().__init__("LoopUnfolding", OptimizeLevel.O2)

    def visit_For(self, node):
        self.generic_visit(node)

        if self.isRangeLoop(node):
            assert isinstance(node.iter, Call)

            evalRange = self.evaluateRange(node.iter)
            if evalRange is None:
                return node

            start, end, step = evalRange

            if (end - start) / step * len(node.body) > Const.LOOP_UNFOLDING_MAX_LINES:
                return node

            body = []

            for i in range(start, end, step):
                target_assignment = Assign(targets=[node.target], value=Constant(value=i))
                body.append(target_assignment)
                body.extend(node.body)

            self.done()
            # return 'Module' object instanced of 'For' object.
            return ast.copy_location(Module(body=body, type_ignores=[]), node)

        return node

    @staticmethod
    def isRangeLoop(node: For):
        return (isinstance(node.iter, Call)
                and isinstance(node.iter.func, Name)
                and node.iter.func.id == range.__name__)
        # TODO If the range function has been overridden, then we will unfold it incorrectly.
        # But I can't check every function in the file and libraries
        # IDK how to fix it

    @staticmethod
    def evaluateRange(rangeExpr: Call) -> Optional[Tuple[int, int, int]]:
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
