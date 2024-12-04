import ast
import typing
from typing import Optional
from ast import Import, ImportFrom, Name, FunctionDef, AST, Store, Call, Constant, ClassDef

from pyfastutil.objects import ObjectArrayList
from pylang_annotations import native

import Const
from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel
from utils.eval.CythonCompiler import CythonCompiler
from utils.source.CodeSource import CodeSource
from utils.source.NativeSource import NativeSource


@native
class NativeConvertor(ITransformer):
    def __init__(self):
        super().__init__("NativeConvertor", OptimizeLevel.O3, post=True)
        self.compiler: Optional[CythonCompiler] = None
        self.funcName: set[str] = set()
        self.existsName: set[str] = set()

    def _init(self):
        if Const.pylang.compilerPath is not None:
            self.compiler = CythonCompiler(Const.pylang.compilerPath)
        elif CythonCompiler.checkCompiler():
            self.compiler = CythonCompiler(CythonCompiler.checkCompiler())
        else:
            self.logger.warn(f"C compiler not available, native optimization will be skipped.")
            return
        self.logger.info(f"Use C compiler: '{self.compiler.compilerPath}'.")

    def _onPreTransform(self) -> None:
        self.funcName.clear()
        self.existsName.clear()
        Const.transManager.updateSources()

    def visit_Module(self, node):
        try:
            newBody = ObjectArrayList(node.body)
            for expr in node.body:
                if isinstance(expr, Import):
                    if not self.handleImport(expr):
                        newBody.remove(expr)
                elif isinstance(expr, ImportFrom):
                    if not self.handleImportFrom(expr):
                        newBody.remove(expr)
            node.body = newBody.to_list()
        except (AttributeError, Exception):
            ...
        return self.generic_visit(node)

    def handleImport(self, node: Import) -> bool:
        for alias in node.names:
            if alias.name == "pylang_annotations":
                if alias.asname is not None:
                    self.funcName.add("pylang_annotations.native")
                else:
                    self.funcName.add(f"{alias.asname}.native")

                if len(node.names) > 1:
                    node.names.remove(alias)
                    return True
                else:
                    return False
        return True

    def handleImportFrom(self, node: ImportFrom):
        if node.module == "pylang_annotations":
            for alias in node.names:
                if alias.name == "native":
                    if alias.asname is not None:
                        self.funcName.add(alias.asname)
                    else:
                        self.funcName.add("native")

                    if len(node.names) > 1:
                        node.names.remove(alias)
                        return True
                    else:
                        return False
        return True

    def tryConvert(self, node: FunctionDef | ClassDef, onlyFunc: bool) -> AST:
        source = Const.transManager.getCurrentSource().copy()
        if onlyFunc:
            source = CodeSource(source.getFilepath(), ast.unparse(node))

        compiled: Optional[NativeSource] = None
        try:
            compiled = self.compiler.compile(source, self.existsName)
        except (IOError, Exception) as e:
            self.logger.debug("Exception while compiling: ", e)

        if compiled is None:
            self.logger.warn(f"Fail to compile {source.getFilename()}, skipped.")
            return self.generic_visit(node)

        Const.transManager.sources.append(compiled)

        importName = compiled.getFilename().removesuffix('.pyd').removesuffix('.so')
        code = f"""
if __name__ == "__main__":
    from {importName} import {node.name}
else:
    from .{importName} import {node.name}
"""

        return ast.parse(code)

    def visit_Name(self, node):
        if isinstance(node.ctx, Store):
            self.existsName.add(node.id)
        return self.generic_visit(node)

    def handle_decorator(self, node: FunctionDef | ClassDef, expr: ast.expr) -> Optional[AST]:
        if isinstance(expr, Name) and expr.id in self.funcName:
            node.decorator_list.remove(expr)
            return self.tryConvert(node, False)
        if isinstance(expr, Call) and isinstance(expr.func, Name) and expr.func.id in self.funcName:
            node.decorator_list.remove(expr)
            onlyFunc = False
            if len(expr.args) > 0:
                if len(expr.args) > 1:
                    self.flag(f"ValueError: excepted 1 arg, got {len(expr.args)}.", *(arg for arg in expr.args[1::]))
                arg = expr.args[0]
                if not isinstance(arg, Constant):
                    self.flag(f"TypeError: excepted a Constant object.", typing.cast(AST, arg))

                onlyFunc = bool(arg.value)

            return self.tryConvert(node, onlyFunc)
        return None

    def visit_FunctionDef(self, node):
        if self.compiler is None:
            return self.generic_visit(node)

        for expr in node.decorator_list:
            result = self.handle_decorator(node, expr)
            if result is not None:
                return result

        return self.generic_visit(node)

    def visit_ClassDef(self, node):
        if self.compiler is None:
            return self.generic_visit(node)

        for expr in node.decorator_list:
            result = self.handle_decorator(node, expr)
            if result is not None:
                return result

        return self.generic_visit(node)
