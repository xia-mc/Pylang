from __future__ import annotations

import ast
from typing import Callable, TypeVar, Optional, Any
from ast import Expr

T = TypeVar("T", bound=Any)
_pure_functions: dict[str, _PureFunction] = {}


class _PureFunction:
    def __init__(self, func: Callable[..., T], toAST: Callable[[T], ast.expr] = None):
        self._func = func
        self._toAST = toAST
        _pure_functions[self._func.__name__] = self

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
    FLOAT = _PureFunction(float)
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
