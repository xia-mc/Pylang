import ast
from ast import Constant, Name, Load, UnaryOp, Not, JoinedStr, FormattedValue
from typing import Optional, Any, Callable

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class FunctionComputer(ITransformer):
    CONSTANT_FUNC: dict[str, Callable] = {
        abs.__name__: abs,
        round.__name__: round,
        pow.__name__: pow,
        divmod.__name__: divmod,
        sum.__name__: sum,
        min.__name__: min,
        max.__name__: max,

        str.__name__: str,
        int.__name__: int,
        float.__name__: float,
        bool.__name__: bool,
        tuple.__name__: tuple,
        list.__name__: list,
        dict.__name__: dict,
        set.__name__: set,

        len.__name__: len,
        sorted.__name__: sorted,
        all.__name__: all,
        any.__name__: any,
        zip.__name__: zip,
        map.__name__: map,
        filter.__name__: filter,
        reversed.__name__: reversed,
        enumerate.__name__: enumerate,
    }

    def __init__(self):
        super().__init__("FunctionComputer", OptimizeLevel.O2)

    def visit_Call(self, node):
        if (isinstance(node.func, Name)
                and isinstance(node.func.ctx, Load)):
            result: Optional[ast.expr]
            try:
                if all(isinstance(obj, Constant) for obj in node.args):
                    result = self.handleConstant(node.func.id, node.args)
                else:
                    result = self.handleOther(node.func.id, node.args)
            except Exception as e:
                self.flag(e, node)
                result = None

            if result is not None:
                self.done()
                return result

        return self.generic_visit(node)

    @staticmethod
    def handleConstant(func: str, args: list[Constant]) -> Optional[Constant]:
        result: Optional[Any] = None
        if func in FunctionComputer.CONSTANT_FUNC:
            result = FunctionComputer.CONSTANT_FUNC[func](*(arg.value for arg in args))

        return Constant(value=result) if result is not None else None

    # noinspection PyTypeChecker
    @staticmethod
    def handleOther(func: str, args: list[ast.expr]) -> Optional[ast.expr]:
        argsLen = len(args)

        result: Optional[ast.expr] = None
        match func:
            case bool.__name__:
                # bool() will result False, but I'm not sure about the possible side effects
                if argsLen == 0:
                    return None
                elif argsLen != 1:
                    raise TypeError(f"bool expected at most 1 argument, got {argsLen}")

                # see https://bilibili.com/video/BV1om4y1F7zv/?t=138
                result = UnaryOp(op=Not(), operand=UnaryOp(op=Not(), operand=args[0]))
            case str.__name__:
                if argsLen > 3:
                    raise TypeError(f"str() takes at most 3 arguments ({argsLen} given)")
                if argsLen != 1:
                    return None
                result = JoinedStr(values=[FormattedValue(value=args[0], conversion=-1)])

        return result
