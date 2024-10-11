from ast import For, Call, Constant, Name
from typing import Any, Optional
import ast


class RangeUtils:
    @staticmethod
    def isRangeLoop(generator: For | ast.comprehension) -> bool:
        return (isinstance(generator.iter, Call)
                and isinstance(generator.iter.func, Name)
                and generator.iter.func.id == range.__name__)

    @staticmethod
    def evaluateRange(rangeExpr: Call) -> Optional[tuple[int, int, int]]:
        def getOrThrow(expr: Any) -> int:
            if isinstance(expr, Constant) and isinstance(expr.value, int):
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
