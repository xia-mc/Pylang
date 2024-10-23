import ast
import os.path
from typing import Optional
from ast import Import, ImportFrom, Name, Module, If

import Const
from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel
from utils.eval.CythonCompiler import CythonCompiler
from utils.source.NativeSource import NativeSource


class NativeConvertor(ITransformer):
    def __init__(self):
        super().__init__("NativeConvertor", OptimizeLevel.O3, post=True)
        self.compiler: Optional[CythonCompiler] = None
        self.funcName: set[str] = set()

    def _init(self):
        if Const.pylang.compilerPath is not None:
            self.compiler = CythonCompiler(Const.pylang.compilerPath)
        elif CythonCompiler.checkCompiler():
            self.compiler = CythonCompiler(CythonCompiler.checkCompiler())
        else:
            self.logger.warn(f"C compiler not available, native optimization will be skipped.")

    def _onPreTransform(self) -> None:
        self.funcName.clear()

    def visit_Module(self, node):
        try:
            for expr in node.body:
                if isinstance(expr, Import):
                    self.handleImport(expr)
                elif isinstance(expr, ImportFrom):
                    self.handleImportFrom(expr)
                else:
                    break
        except (AttributeError, Exception):
            ...
        return self.generic_visit(node)

    def handleImport(self, node: Import):
        for alias in node.names:
            if alias.name == "pylang_annotations.annotations":
                if alias.asname is not None:
                    self.funcName.add(f"{alias.asname}.native")
                else:
                    self.funcName.add("pylang_annotations.native")
                    self.funcName.add("pylang_annotations.annotations.native")
            elif alias.name == "pylang_annotations":
                if alias.asname is not None:
                    self.funcName.add("pylang_annotations.native")
                    self.funcName.add("pylang_annotations.annotations.native")
                else:
                    self.funcName.add(f"{alias.asname}.native")
                    self.funcName.add(f"{alias.asname}.annotations.native")

    def handleImportFrom(self, node: ImportFrom):
        if node.module == "pylang_annotations":
            for alias in node.names:
                if alias.name == "native":
                    if alias.asname is not None:
                        self.funcName.add(alias.asname)
                    else:
                        self.funcName.add("native")
                elif alias.name == "annotations":
                    if alias.asname is not None:
                        self.funcName.add(f"{alias.asname}.native")
                    else:
                        self.funcName.add("annotations.native")
        elif node.module == "pylang_annotations.annotations":
            for alias in node.names:
                if alias.name == "native":
                    if alias.asname is not None:
                        self.funcName.add(alias.asname)
                    else:
                        self.funcName.add("native")

    def visit_FunctionDef(self, node):
        if self.compiler is None:
            return self.generic_visit(node)

        if any((isinstance(expr, Name) and expr.id in self.funcName) for expr in node.decorator_list):
            # force native
            compiled: Optional[NativeSource] = None
            try:
                compiled = self.compiler.compile(Const.transManager.getCurrentSource())
            except (IOError, Exception) as e:
                self.logger.debug("Exception while compiling: ", e)

            if compiled is None:
                self.logger.warn(f"Fail to compile {Const.transManager.getCurrentSource().getFilename()}, skipped.")
                return self.generic_visit(node)

            Const.transManager.sources.append(compiled)

            code = f"""if __name__ == "__main__":
    from {compiled.getFilename().removesuffix('.pyd')} import {node.name}
else:
    from .{compiled.getFilename().removesuffix('.pyd')} import {node.name}
"""

            return ast.parse(code)

        return self.generic_visit(node)
