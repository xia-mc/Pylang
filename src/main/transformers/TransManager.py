from __future__ import annotations

import ast
import time
from ast import ImportFrom, Import
from ast import Module
from typing import Type, TextIO, TYPE_CHECKING, Optional, TypeVar

from colorama import Fore
from pyfastutil.objects import ObjectArrayList
from tqdm import tqdm

import Const
from log.Logger import Logger
from transformers.OptimizeLevel import OptimizeLevel
from transformers.impl.O0.DocumentRemover import DocumentRemover
from transformers.impl.O1.ConstantFolding import ConstantFolding
from transformers.impl.O1.DeadCodeElimination import DeadCodeElimination
from transformers.impl.O2.FunctionComputer import FunctionComputer
from transformers.impl.O2.LoopUnfolding import LoopUnfolding
from transformers.impl.O2.VariableRenamer import VariableRenamer
from transformers.impl.O3.NativeConvertor import NativeConvertor
from utils.source.CodeSource import CodeSource
from utils.source.Source import Source

if TYPE_CHECKING:
    from transformers.ITransformer import ITransformer
    T = TypeVar("T", bound=ITransformer)


class TransManager:
    def __init__(self, logger: Logger, level: OptimizeLevel):
        Const.transManager = self
        self.logger = logger
        self.level = level
        self.sources: list[Source] = ObjectArrayList()
        # Raw sources from file. key: filename, value: Source object.
        self.modules: dict[CodeSource, Module] = {}
        self.transformers: dict[Type[T], T] = {}

        # state while transforming
        self.curSource: Optional[CodeSource] = None
        self.curModule: Optional[Module] = None

    def register(self):
        def doRegister(transformer: ITransformer):
            self.transformers[type(transformer)] = transformer
            transformer.init()

        doRegister(ConstantFolding())
        doRegister(DeadCodeElimination())
        doRegister(LoopUnfolding())
        doRegister(DocumentRemover())
        # doRegister(UnusedVariableRemover())  # unstable, can't eval class correctly
        doRegister(VariableRenamer())
        doRegister(FunctionComputer())
        doRegister(NativeConvertor())
        # doRegister(PredictEngineImpl())

    def parse(self, filename: str):
        def checkModule(mod: Module) -> bool:
            try:
                for expr in mod.body:
                    if not isinstance(expr, ImportFrom) and not isinstance(expr, Import):
                        return True
                    if (isinstance(expr, ImportFrom) and
                            expr.module == "pylang_annotations" and "skip_module" in expr.names):
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
                    self.curModule = module

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

                        # Make sure there's nothing to optimize
                        if transformer.isChanged():
                            isFinish = False

        self.logger.debug(f"General-Transform done in {cycle} cycle.")

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

        self.updateSources()
        return self.sources

    def updateSources(self) -> None:
        """
        Update sources attr from modules
        """
        if len(self.modules) == 0 and len(self.sources) == 0:
            return

        newSources: list[Source] = ObjectArrayList()
        for source, module in self.modules.items():
            code = ast.unparse(module)
            newSources.append(CodeSource(source.getFilepath(), code))
            source.setSources(code)

        existSources = {e.getFilepath() for e in newSources}
        for source in self.sources:
            filename = source.getFilepath()
            if filename not in existSources:
                newSources.append(source)
                existSources.add(filename)

        self.sources = newSources
        self.curSource = next(filter(lambda s: s.getFilepath() == self.getCurrentSource().getFilepath(), self.sources))

    def getCurrentSource(self) -> Optional[CodeSource]:
        return self.curSource

    def getCurrentModule(self) -> Optional[Module]:
        return self.curModule
