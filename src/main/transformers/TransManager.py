from __future__ import annotations

import ast
from ast import Module
from typing import Type, TextIO, TYPE_CHECKING

from tqdm import tqdm

import Const
from log.Logger import Logger
from parsers.Source import Source
from transformers.OptimizeLevel import OptimizeLevel
from transformers.impl.O1.ConstantFolding import ConstantFolding
from transformers.impl.O1.DeadCodeElimination import DeadCodeElimination
from transformers.impl.O0.DocumentRemover import DocumentRemover
from transformers.impl.O0.VariableRenamer import VariableRenamer
from transformers.impl.O2.LoopUnfolding import LoopUnfolding
from transformers.impl.O2.UnusedVariableRemover import UnusedVariableRemover

if TYPE_CHECKING:
    from Pylang import Pylang
    from transformers.ITransformer import ITransformer


class TransManager:
    def __init__(self, pylang: Pylang, logger: Logger, level: OptimizeLevel):
        Const.transManager = self
        self.pylang = pylang
        self.logger = logger
        self.level = level
        self.sources: list[Source] = []
        """Raw sources from file. key: filename, value: Source object."""
        self.modules: dict[Source, Module] = {}
        self.transformers: dict[Type[ITransformer], ITransformer] = {}

    def register(self):
        def doRegister(transformer: ITransformer):
            self.transformers[type(transformer)] = transformer
            transformer.onRegister()

        doRegister(ConstantFolding())
        doRegister(DeadCodeElimination())
        doRegister(LoopUnfolding())
        doRegister(DocumentRemover())
        doRegister(UnusedVariableRemover())
        doRegister(VariableRenamer())
        # doRegister(VariableInliner())

    def parse(self, filename: str):
        try:
            file = self.toFile(filename)
            source = Source(file.name[1::], file.read())
            self.sources.append(source)

            module = ast.parse(source.getSources())
            self.logger.debug(f"Find module in source {file.name} with {len(module.body)} ast objects.")
            self.modules[source] = module

            for transformer in self.transformers.values():
                transformer.onParseModule(module, source)
        except Exception as e:
            self.logger.warn(f"Failed to parse {filename}. ignored.")
            self.logger.debug(type(e).__name__, ": ", str(e))

    @staticmethod
    def toFile(filename: str) -> TextIO:
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
        while not isFinish:
            cycle += 1
            isFinish = True

            self.logger.info(f"Transforming cycle: {cycle}")
            with tqdm(total=len(self.transformers) * 4 * len(self.modules.items())) as progress:
                for source, module in self.modules.items():
                    transformed = 0
                    for transformer in self.transformers.values():
                        if not transformer.checkLevel():
                            progress.update(4)
                            continue

                        progress.set_description(f"{transformer.name}: Pre")
                        progress.update()
                        transformer.onPreTransform()

                        progress.set_description(f"{transformer.name}: Visit")
                        progress.update()
                        module = transformer.visit(module)

                        progress.set_description(f"{transformer.name}: Post")
                        progress.update()
                        transformer.onPostTransform()

                        progress.set_description(f"{transformer.name}: Fixing-locations")
                        progress.update()
                        ast.fix_missing_locations(module)

                        transformed += 1
                        # Make sure there's nothing to optimize
                        if transformer.isChanged():
                            isFinish = False
                            # progress.update((len(self.transformers) - transformed) * 4)
                            # break
                self.modules[source] = module
                # self.logger.debug(ast.unparse(module))
        self.logger.info("Transform done!")

        result: list[Source] = []
        for source, module in self.modules.items():
            result.append(Source(source.getFilename(), ast.unparse(module)))

        existSources = {e.getFilename() for e in result}
        for source in self.sources:
            filename = source.getFilename()
            if filename not in existSources:
                result.append(source)
                existSources.add(filename)

        return result
