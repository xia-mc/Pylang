import ast
import typing
from ast import (NotEq, AST, In, Constant, NotIn, Lt, Is, Eq, Gt, Name, IsNot, GtE, Assign, Compare, LtE,
                 NodeTransformer, Pass, Module, Load, Call, Lambda, FunctionDef, Return, BinOp, Add, BitAnd,
                 BitOr, BitXor, Div, FloorDiv, LShift, MatMult, Mod, Mult, Pow, RShift, Sub)
from typing import Any

from pylang_annotations import native

from utils.ASTUtils import ASTUtils
from utils.simulation.Interrupts import EvalException
from utils.simulation.PredictEngine import PredictEngine, T
from utils.simulation.Variable import Variable
from utils.simulation.objects.PyFunction import PyFunction
from utils.simulation.objects.PyObject import PyObject


@native
class PredictEngineImpl(PredictEngine):
    MAX_PREDICT_DEPTH = 100

    def __init__(self):
        super().__init__()
        self._predictDepth = 0

    def reset(self, parent: AST) -> None:
        super().reset(parent)
        self._predictDepth = 0

    def _visit(self, node: T) -> T:
        if self._predictDepth >= self.MAX_PREDICT_DEPTH:
            self.flag("Eval overflow! Something may went wrong!", self.visiting)
            self._predictDepth -= 1
            return node

        self._predictDepth += 1

        result: AST = node
        if isinstance(node, Assign):
            result = self.handleAssign(node)
        elif isinstance(node, Compare):
            result = self.handleCompare(node)
        elif isinstance(node, Module):
            result = self.handleModule(node)
        elif isinstance(node, Name):
            result = self.handleName(node)
        elif isinstance(node, Call):
            result = self.handleCall(node)
        elif isinstance(node, FunctionDef):
            result = self.handleFunctionDef(node)
        elif isinstance(node, Return):
            result = self.handleReturn(node)
        elif isinstance(node, BinOp):
            result = self.handleBinOp(node)

        self._predictDepth -= 1

        if result is not node:
            self.done()
        return result

    def getVariable(self, node: ast.expr) -> Variable:
        pyObject = ASTUtils.toPyObject(self, node)
        return Variable(pyObject, pyObject.type())

    def handleAssign(self, node: Assign) -> AST:
        var = self.getVariable(node.value)

        for target in node.targets:
            assert isinstance(target, Name)
            self.put(target.id, var)

            local = self.locals()

            def removeUnused():
                assert isinstance(target, Name)
                if not self.get(target.id).isNeverUse():
                    return

                # do remove
                removed = False

                if len(node.targets) > 1:
                    node.targets.remove(target)

                class UnusedRemover(NodeTransformer):
                    def visit_Assign(self, n):
                        nonlocal removed
                        if n is not node:
                            return self.generic_visit(n)
                        removed = True
                        if isinstance(node.value, Constant):
                            return Pass()
                        return node.value

                UnusedRemover().visit(local.parent)

                if removed:
                    self.done()

            local.executeOnPost(removeUnused)
        return node

    def handleCompare(self, node: Compare) -> AST:
        assert len(node.ops) > 0
        assert len(node.ops) == len(node.comparators)
        for i in range(len(node.ops)):
            op = type(node.ops[i])
            leftAST = self.getVariable(node.left if i == 0 else node.comparators[i - 1]).get()
            rightAST = self.getVariable(node.comparators[i]).get()

            if leftAST is None or rightAST is None:  # can't eval
                return node

            result: bool
            try:
                left = leftAST.toObject()
                right = rightAST.toObject()

                if op is Eq:
                    result = left == right
                elif op is NotEq:
                    result = left != right
                elif op is Lt:
                    result = left < right
                elif op is LtE:
                    result = left <= right
                elif op is Gt:
                    result = left > right
                elif op is GtE:
                    result = left >= right
                elif op is Is:
                    result = left is right
                elif op is IsNot:
                    result = left is not right
                elif op is In:
                    result = left in right
                elif op is NotIn:
                    result = left not in right
                else:
                    assert False
            except EvalException:
                return node
            except Exception as e:
                self.throw(e)
                return node

            if not result:
                return Constant(value=False)

        return Constant(value=True)

    def handleModule(self, node: Module) -> AST:
        newBody = []
        for n in node.body:
            if type(n) is Pass:
                self.done()
                continue
            newBody.append(n)

        node.body = newBody
        return node

    def handleName(self, node: Name) -> AST:
        if not isinstance(node.ctx, Load):
            return node

        # try to inline
        pyObject = self.get(node.id).get()
        if pyObject is None:
            return node
        expr = pyObject.toConstExpr()
        if expr is None:
            return node
        return expr

    def handleCall(self, node: Call) -> AST:
        if isinstance(node.func, Name):
            assert isinstance(node.func.ctx, Load)
            var = self.get(node.func.id)
            func = var.get()
        elif isinstance(node.func, Lambda):
            func = PyFunction(self, node.func)
        else:
            return node

        args: tuple[PyObject, ...] = tuple(ASTUtils.toPyObject(self, arg) for arg in node.args)
        kwargs: dict[str, PyObject] = {keyword.arg: ASTUtils.toPyObject(self, keyword.value) for keyword in
                                       node.keywords}

        # call
        try:
            result = func.call(*args, **kwargs)
            if result[1]:
                expr = result[0].toConstExpr()
                if expr is not None:
                    # pre-compute
                    return expr
        except EvalException:
            ...
        except Exception as e:
            self.throw(e)
            return node

        # inline
        expr = func.toConstExpr()
        if expr is not None:
            if isinstance(expr, Call):
                return expr
            else:
                node.func = expr
                self.done()
                return node
        return node

    def handleFunctionDef(self, node: FunctionDef) -> AST:
        node = typing.cast(FunctionDef, self.handleModule(typing.cast(Module, node)))

        obj = PyFunction(self, node)
        self.put(node.name, Variable(obj, obj.type()))

        local = self.locals()

        def removeUnused():
            if not self.get(node.name).isNeverUse():
                return

            # do remove
            removed = False

            class UnusedRemover(NodeTransformer):
                def visit_FunctionDef(self, n):
                    nonlocal removed
                    if n is not node:
                        return self.generic_visit(n)
                    removed = True
                    return Pass()

            UnusedRemover().visit(local.parent)

            if removed:
                self.done()

        local.executeOnPost(removeUnused)

        return node

    def handleReturn(self, node: Return) -> AST:
        self.interruptManager.returns(ASTUtils.toPyObject(self, node.value))
        return node

    def handleBinOp(self, node: BinOp) -> AST:
        op = type(node.op)
        leftAST = self.getVariable(node.left).get()
        rightAST = self.getVariable(node.right).get()

        if leftAST is None or rightAST is None:  # can't eval
            return node

        result: Any
        try:
            left: Any = leftAST.toObject()
            right: Any = rightAST.toObject()

            if op is Add:
                result = left + right
            elif op is BitAnd:
                result = left & right
            elif op is BitOr:
                result = left | right
            elif op is BitXor:
                result = left ^ right
            elif op is Div:
                result = left / right
            elif op is FloorDiv:
                result = left // right
            elif op is LShift:
                result = left << right
            elif op is MatMult:
                result = left @ right
            elif op is Mod:
                result = left % right
            elif op is Mult:
                result = left * right
            elif op is Pow:
                result = left ** right
            elif op is RShift:
                result = left >> right
            elif op is Sub:
                result = left - right
            else:
                assert False
        except EvalException:
            return node
        except Exception as e:
            self.throw(e)
            return node

        expr = ASTUtils.toPyObject(self, result).toConstExpr()
        if expr is None:
            return node
        return expr
