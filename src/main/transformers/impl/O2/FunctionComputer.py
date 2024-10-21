import ast
from ast import Constant, Name, Load, UnaryOp, Not, JoinedStr, FormattedValue, List, Set, Dict, Tuple
from typing import Optional, Any, Iterable

from numba import njit

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel
from utils.PureFunctions import PureFunctions


class FunctionComputer(ITransformer):
    def __init__(self):
        super().__init__("FunctionComputer", OptimizeLevel.O2)

    # noinspection PyTypeChecker
    def visit_Call(self, node):
        if (isinstance(node.func, Name)
                and isinstance(node.func.ctx, Load)):
            result: Optional[ast.expr]
            try:
                if self.isConstantObj(node.args + [kw.value for kw in node.keywords]):
                    result = self.handleConstant(node.func.id, node.args, node.keywords)
                else:
                    result = self.handleOther(node.func.id, node.args, node.keywords)
            except Exception as e:
                self.flag(e, node)
                result = None

            if result is not None:
                self.done()
                return result

        return self.generic_visit(node)

    @staticmethod
    def isConstantObj(objs: Iterable[ast.expr]):
        for obj in objs:
            if isinstance(obj, List) or isinstance(obj, Set) or isinstance(obj, Dict) or isinstance(obj, Tuple):
                if not FunctionComputer.isConstantObj(obj.elts):
                    return False
            elif not isinstance(obj, Constant):
                return False
        return True

    @staticmethod
    def handleConstant(func: str, args: list[Constant], kwargs: list[ast.keyword]) -> Optional[ast.expr]:
        # noinspection PyUnresolvedReferences
        # ensure isinstance(kw.value, Constant)
        return PureFunctions.call(func, *(arg.value for arg in args), **{kw.arg: kw.value.value for kw in kwargs})

    # noinspection PyTypeChecker
    @staticmethod
    def handleOther(func: str, args: list[ast.expr], kwargs: list[ast.keyword]) -> Optional[ast.expr]:
        argsLen = len(args)
        kwargsLen = len(kwargs)

        result: Optional[ast.expr] = None
        match func:
            case bool.__name__:
                # bool() will result False, but I'm not sure about the possible side effects
                if kwargsLen != 0:
                    raise TypeError("bool() takes no keyword arguments")
                if argsLen == 0:
                    return None
                elif argsLen != 1:
                    raise TypeError(f"bool expected at most 1 argument, got {argsLen}")

                # see https://bilibili.com/video/BV1om4y1F7zv/?t=138
                result = UnaryOp(op=Not(), operand=UnaryOp(op=Not(), operand=args[0]))
            case str.__name__:
                if argsLen > 3:
                    raise TypeError(f"str() takes at most 3 arguments ({argsLen} given)")
                if argsLen == 1:
                    result = JoinedStr(values=[FormattedValue(value=args[0], conversion=-1)])
                elif kwargsLen == 1 and kwargs[0].arg == "object":
                    result = JoinedStr(values=[FormattedValue(value=kwargs[0].value, conversion=-1)])
                else:
                    return None

        return result
