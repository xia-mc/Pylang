from __future__ import annotations

import ast
import math
import typing
from ast import Expr, Constant
from typing import Callable, TypeVar, Optional, Any

from pylang_annotations import native

T = TypeVar("T", bound=Any)
_pure_functions: dict[str, _PureFunction] = {}


@native
class _PureFunction:
    def __init__(self, func: Callable[..., T], toAST: Callable[[T], ast.expr] = None):
        self._func = func
        self._toAST = toAST
        _pure_functions[self._func.__name__] = self

    def getFunc(self):
        return self._func

    def call(self, *args, **kwargs) -> Optional[ast.expr]:
        pyRes = self._func(*args, **kwargs)
        if self._toAST is not None:
            return self._toAST(pyRes)

        try:
            expr = ast.parse(str(pyRes)).body[0]
            assert isinstance(expr, Expr)
            return expr.value
        except (SyntaxError, AssertionError, TypeError, ValueError, Exception):
            return None


INF: ast.expr = typing.cast(ast.Expr, ast.parse("__import__('math').inf").body[0]).value
NAN: ast.expr = typing.cast(ast.Expr, ast.parse("__import__('math').nan").body[0]).value


@native
class PureFunctions:
    ABS = _PureFunction(abs)
    ROUND = _PureFunction(round)
    POW = _PureFunction(pow)
    DIVMOD = _PureFunction(divmod)
    SUM = _PureFunction(sum)
    MIN = _PureFunction(min)
    MAX = _PureFunction(max)

    STR = _PureFunction(str)
    INT = _PureFunction(int)
    FLOAT = _PureFunction(float, lambda f: INF if math.isinf(f) else NAN if math.isnan(f) else Constant(value=f))
    BOOL = _PureFunction(bool)
    TUPLE = _PureFunction(tuple)
    LIST = _PureFunction(list)
    DICT = _PureFunction(dict)
    SET = _PureFunction(set)

    LEN = _PureFunction(len)
    SORTED = _PureFunction(sorted)
    ALL = _PureFunction(all)
    ANY = _PureFunction(any)

    # ZIP = _PureFunction(zip, _generatorToAST)
    # MAP = _PureFunction(map, _generatorToAST)
    # FILTER = _PureFunction(filter, _generatorToAST)
    # REVERSED = _PureFunction(reversed, _generatorToAST)
    # ENUMERATE = _PureFunction(enumerate, _generatorToAST)

    @staticmethod
    def call(name: str, *args, **kwargs) -> Optional[ast.expr]:
        """
        Try to find and call the function with args
        maybe throw exception
        :param name: the name of the function
        :param args: args to call function
        :return: the ast node with the result
        """
        func = _pure_functions.get(name, None)
        if func is None:
            return None

        return func.call(*args, **kwargs)

    @staticmethod
    def isPure(func: Callable) -> bool:
        return any(func is f.getFunc() for f in _pure_functions.values())
