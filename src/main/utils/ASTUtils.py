from __future__ import annotations

import ast
from ast import Name, Call, Lambda, Attribute, GeneratorExp, Load, Tuple, Store, Constant, List, Set, Dict, AST, \
    FunctionDef, Expr
from types import NoneType
from typing import overload, Optional, Collection, TYPE_CHECKING, TypeVar

from pyfastutil.objects import ObjectArrayList

from utils.simulation.TypeUtils import TypeUtils

if TYPE_CHECKING:
    from utils.simulation.PredictEngine import PredictEngine
    from utils.simulation.objects.PyObject import PyObject


T = TypeVar("T", bound=AST)


class ASTUtils:
    @staticmethod
    @overload
    def raiseExpr(exception: Exception) -> Call:
        ...

    @staticmethod
    def raiseExpr(exception: Name, *args: str) -> Call:
        if isinstance(exception, Exception):
            args = [str(arg) for arg in exception.args]
            exception = Name(id=type(exception).__name__, ctx=Load())

        return Call(
            func=Lambda(
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[]),
                body=Call(
                    func=Attribute(
                        value=GeneratorExp(
                            elt=Name(id='_', ctx=Load()),
                            generators=[
                                ast.comprehension(
                                    target=Name(id='_', ctx=Store()),
                                    iter=Tuple(elts=[], ctx=Load()),
                                    ifs=[],
                                    is_async=0)]),
                        attr='throw',
                        ctx=Load()),
                    args=[
                        Call(
                            func=exception,
                            args=[Constant(value=arg) for arg in args],
                            keywords=[])],
                    keywords=[])),
            args=[],
            keywords=[])

    @staticmethod
    def toExpr(obj: object) -> Optional[ast.expr]:
        """
        如果可能，转换为ast expr
        不要传入包含自引用的对象
        """

        def collectionToElt(o: Collection) -> list[ast.expr]:
            objs = ObjectArrayList(len(o))
            for value in o:
                o = ASTUtils.toExpr(value)
                if o is None:
                    raise ValueError()
                objs.append(o)
            return objs.to_list()

        typ = type(obj)
        try:
            if typ in (int, float, str, NoneType, Ellipsis, NotImplemented):
                return Constant(value=obj)
            elif typ is list:
                assert isinstance(obj, list)
                values = collectionToElt(obj)
                return List(elts=values, ctx=Load())
            elif typ is tuple:
                assert isinstance(obj, tuple)
                values = collectionToElt(obj)
                return Tuple(elts=values, ctx=Load())
            elif typ is set:
                assert isinstance(obj, set)
                values = collectionToElt(obj)
                return Set(elts=values)
            elif typ is dict:
                assert isinstance(obj, dict)
                keys = collectionToElt(obj.keys())
                values = collectionToElt(obj.values())
                return Dict(keys=keys, values=values)
        except ValueError:
            ...
        return None

    @staticmethod
    def toPyObject(engine: PredictEngine, obj: AST | object) -> PyObject:
        from utils.simulation.objects.PyConstant import PyConstant, T
        from utils.simulation.objects.PyFunction import PyFunction
        from utils.simulation.objects.PyUnknown import PyUnknown

        # assert not isinstance(obj, PyObject)  # I cost TOO MANY times to fix this bug

        if isinstance(obj, Name):
            assert isinstance(obj.ctx, Load)
            return engine.get(obj.id).get()

        if isinstance(obj, Constant) or TypeUtils.checkMatchTypeVar(obj, T):
            return PyConstant(engine, obj)
        elif isinstance(obj, FunctionDef) or callable(obj):
            return PyFunction(engine, obj)

        return PyUnknown(engine)

    @staticmethod
    def deepcopy(node: T) -> T:
        assert isinstance(node, AST)

        res = ast.parse(ast.unparse(node)).body[0]
        if isinstance(node, ast.expr):
            if isinstance(res, Expr):
                return res.value

        return res
