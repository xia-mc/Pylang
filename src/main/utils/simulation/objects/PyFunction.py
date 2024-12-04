from __future__ import annotations

import ast
from ast import FunctionDef, Lambda, NodeTransformer, AST, Expr
from typing import Optional, Callable, TYPE_CHECKING

from pylang_annotations import native

from utils.ASTUtils import ASTUtils
from utils.simulation.Interrupts import Type, EvalException
from utils.simulation.Variable import Variable
from utils.simulation.objects.PyConstant import PyConstant
from utils.simulation.objects.PyObject import PyObject
from utils.simulation.objects.PyUnknown import PyUnknown

if TYPE_CHECKING:
    from utils.simulation.PredictEngine import PredictEngine


@native
class PyFunction(PyObject):
    def __init__(self, engine: PredictEngine, obj: FunctionDef | Lambda | Callable):
        super().__init__(engine)
        self.__obj = obj
        self.__callable = True

        if callable(self.__obj):
            return

        if isinstance(self.__obj, FunctionDef):
            self.__name = obj.name
            self.__body: list[AST] = obj.body
        else:
            self.__name = "<lambda>"
            self.__body: list[AST] = [obj.body]

        self.__defaultArgs: list[PyObject] = \
            [ASTUtils.toPyObject(engine, obj) for obj in self.__obj.args.defaults]
        self.__defaultKwargs: dict[str, PyObject] = \
            {arg.arg: ASTUtils.toPyObject(engine, obj) for arg, obj in
             zip(self.__obj.args.kwonlyargs, self.__obj.args.kw_defaults)}

        if (any(isinstance(obj, PyUnknown) for obj in self.__defaultArgs)
                or any(isinstance(obj, PyUnknown) for obj in self.__defaultKwargs)):
            self.__defaultArgs.clear()
            self.__defaultKwargs.clear()
            self.__callable = False

    def getObj(self) -> FunctionDef | Lambda | Callable:
        return self.__obj

    def call(self, *args: PyObject, **kwargs: PyObject) -> tuple[PyObject, bool]:
        if not self.__callable:
            raise EvalException()
        if callable(self.__obj):  # 所有传入PyFunction的callable一定能在编译时求值（constexpr）
            objArgs = tuple(arg.toObject() for arg in args)
            objKwargs = {k: v.toObject() for k, v in kwargs.items()}
            return ASTUtils.toPyObject(self.engine, self.__obj(*objArgs, **objKwargs)), True

        isPure = True
        self.engine.pushMatrix()
        try:
            self.parseArgs(args, kwargs)

            class PureChecker(NodeTransformer):
                def visit_Call(self, node):
                    nonlocal isPure
                    isPure = False
                    return self.generic_visit(node)

            pureChecker = PureChecker()

            for stmt in self.__body:
                self.engine.visit(stmt)
                if isPure:
                    # 假设：所有纯函数都能在编译时求值
                    pureChecker.visit(stmt)

                if self.engine.interruptManager.getContext() is not None:
                    context = self.engine.interruptManager.getContext()
                    if context.getType() == Type.RETURN:
                        self.engine.interruptManager.finish()
                        return context.getValue(), isPure
                    return PyUnknown(self.engine), False

            return PyConstant(self.engine, None), isPure
        finally:
            self.engine.popMatrix()

    def parseArgs(self, args: tuple[PyObject, ...], kwargs: dict[str, PyObject]) -> None:
        arguments: ast.arguments = self.__obj.args

        if len(args) < len(arguments.posonlyargs) - len(self.__defaultArgs):
            raise TypeError(f"{self.__name}() missing required positional arguments.")
        if len(kwargs) < len(arguments.kwonlyargs) - len(self.__defaultKwargs):
            raise TypeError(f"{self.__name}() missing required keyword arguments.")

        argsRequired = self.getArgsRequired()
        if len(args) + len(kwargs) < argsRequired - len(self.__defaultArgs) + len(self.__defaultKwargs):
            raise TypeError(f"{self.__name}() missing required keyword arguments.")
        elif len(args) + len(kwargs) > argsRequired:
            raise TypeError(f"{self.__name}() got multiple values for arguments.")

        argsIter = iter(args)

        for arg in arguments.posonlyargs:
            value = next(argsIter)
            self.engine.put(arg.arg, Variable(value, value.type()))
            argsRequired -= 1

        for arg in arguments.kwonlyargs:
            if arg.arg not in kwargs:
                continue
            value = kwargs[arg.arg]
            self.engine.put(arg.arg, Variable(value, value.type()))
            argsRequired -= 1

        defaultArgsIter = iter(self.__defaultArgs)
        for arg in arguments.args:
            value = next(argsIter, None)
            if value is None:
                value = kwargs.get(arg.arg, None)
            if value is None:
                value = next(defaultArgsIter, None)
            if value is None:
                value = self.__defaultKwargs.get(arg.arg, None)
            if value is None:
                raise TypeError(f"{self.__name}() missing required arguments.")

            self.engine.put(arg.arg, Variable(value, value.type()))

    def getArgsRequired(self) -> int:
        return len(self.__obj.args.posonlyargs) + len(self.__obj.args.kwonlyargs) + len(self.__obj.args.args)

    def toConstExpr(self) -> Optional[ast.expr]:
        if isinstance(self.__obj, Lambda):
            return self.__obj
        elif isinstance(self.__obj, FunctionDef) and len(self.__body) == 1:
            astObj = self.__body[0]

            if isinstance(astObj, Expr):
                astObj = astObj.value
            elif not isinstance(astObj, ast.expr):
                return None

            if self.getArgsRequired() == 0:
                return astObj
            else:
                Lambda(
                    args=self.__obj.args,
                    body=astObj
                )
        return None

    def toObject(self) -> Callable:
        if callable(self.__obj):
            return self.__obj
        return self.call

    def getName(self) -> str:
        return self.__name
