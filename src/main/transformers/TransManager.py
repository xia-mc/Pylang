from __future__ import annotations

import ast
import time
from ast import Module
from typing import Type, TextIO, TYPE_CHECKING, Optional
from ast import ImportFrom

import pylang_annotations

from colorama import Fore
from tqdm import tqdm

import Const
from log.Logger import Logger
from transformers.impl.O2.FunctionComputer import FunctionComputer
from transformers.impl.O3.NativeConvertor import NativeConvertor
from utils.source.CodeSource import CodeSource
from transformers.OptimizeLevel import OptimizeLevel
from transformers.impl.O0.DocumentRemover import DocumentRemover
from transformers.impl.O1.ConstantFolding import ConstantFolding
from transformers.impl.O1.DeadCodeElimination import DeadCodeElimination
from transformers.impl.O2.LoopUnfolding import LoopUnfolding
from transformers.impl.O2.UnusedVariableRemover import UnusedVariableRemover
from transformers.impl.O2.VariableRenamer import VariableRenamer
from utils.source.Source import Source

if TYPE_CHECKING:
    from transformers.ITransformer import ITransformer


class TransManager:
    def __init__(self, logger: Logger, level: OptimizeLevel):
        Const.transManager = self
        self.logger = logger
        self.level = level
        self.sources: list[Source] = []
        # Raw sources from file. key: filename, value: Source object.
        self.modules: dict[CodeSource, Module] = {}
        self.transformers: dict[Type[ITransformer], ITransformer] = {}

        # state while transforming
        self.curSource: Optional[CodeSource] = None

    def register(self):
        def doRegister(transformer: ITransformer):
            self.transformers[type(transformer)] = transformer
            transformer.init()

        doRegister(ConstantFolding())
        doRegister(DeadCodeElimination())
        doRegister(LoopUnfolding())
        doRegister(DocumentRemover())
        doRegister(UnusedVariableRemover())
        doRegister(VariableRenamer())
        doRegister(FunctionComputer())
        doRegister(NativeConvertor())

    def parse(self, filename: str):
        def checkModule(mod: Module) -> bool:
            try:
                for expr in mod.body:
                    if not isinstance(expr, ImportFrom):
                        return True
                    if (expr.module == pylang_annotations.__name__
                            or expr.module == pylang_annotations.features.__name__):
                        return False
            except (AttributeError, Exception):
                ...
            return True

        try:
            file = self._toFile(filename)
            source = CodeSource(file.name.replace("\\", "/"), file.read())
            self.sources.append(source)

            module = ast.parse(source.getSources())
            self.logger.debug(f"Find module in source {Fore.CYAN}{source.getFilepath()}{Fore.RESET} "
                              f"with {len(module.body)} ast objects.")
            if checkModule(module):
                self.modules[source] = module
            else:
                self.logger.debug(f"Skipped module in source {source.getFilepath()}.")

            for transformer in self.transformers.values():
                transformer.onParseModule(module, source)
        except SyntaxError as e:
            self.logger.warn(f"Failed to parse {filename}. skipped.")
            self.logger.debug(type(e).__name__, ": ", str(e))

    @staticmethod
    def _toFile(filename: str) -> TextIO:
        # 添加更多的编码格式
        codecs = ["UTF-8", "UTF-16", "ISO-8859-1", "GBK", "ASCII"]

        for codec in codecs:
            try:
                file = open(filename, encoding=codec)
                return file
            except (UnicodeDecodeError, FileNotFoundError):
                pass

        raise IOError(f"File {filename} can't be decoded with any supported encoding.")

    def transform(self) -> list[Source]:
        cycle = 0
        isFinish = False
        startTime = time.perf_counter()

        while not isFinish:
            cycle += 1
            isFinish = True

            with tqdm(
                    total=len(self.transformers) * 4 * len(self.modules.items()),
                    leave=False,
                    desc=f"Transforming cycle: {cycle}"
            ) as progress:
                for source, module in self.modules.items():
                    self.curSource = source

                    transformed = 0
                    for transformer in self.transformers.values():
                        if (not transformer.checkLevel()) or transformer.post:
                            progress.update(4)
                            continue

                        progress.update()
                        transformer.onPreTransform()

                        progress.update()
                        module = transformer.visit(module)

                        progress.update()
                        transformer.onPostTransform()

                        progress.update()
                        ast.fix_missing_locations(module)

                        transformed += 1
                        # Make sure there's nothing to optimize
                        if transformer.isChanged():
                            isFinish = False

        postTransformers: list[ITransformer] = [i for i in self.transformers.values() if i.post and i.checkLevel()]
        with tqdm(
                total=len(postTransformers) * 4 * len(self.modules.items()),
                leave=False,
                desc=f"Transforming post"
        ) as progress:
            for source, module in self.modules.items():
                self.curSource = source

                for transformer in postTransformers:
                    progress.update()
                    transformer.onPreTransform()

                    progress.update()
                    module = transformer.visit(module)

                    progress.update()
                    transformer.onPostTransform()

                    progress.update()
                    ast.fix_missing_locations(module)

        self.logger.info(f"Transform done! Cost {time.perf_counter() - startTime:.3f}s")

        result: list[Source] = []
        for source, module in self.modules.items():
            result.append(CodeSource(source.getFilepath(), ast.unparse(module)))

        existSources = {e.getFilepath() for e in result}
        for source in self.sources:
            filename = source.getFilepath()
            if filename not in existSources:
                result.append(source)
                existSources.add(filename)

        return result

    def getCurrentSource(self) -> Optional[CodeSource]:
        return self.curSource
