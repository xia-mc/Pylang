from __future__ import annotations

from dataclasses import dataclass

from utils.source.Source import Source


@dataclass
class CodeSource(Source):
    __filepath: str
    __sources: str

    def getFilepath(self):
        return self.__filepath

    def writeToFile(self, path) -> None:
        with open(path, "w") as f:
            f.write(self.getSources())

    def getSources(self):
        return self.__sources

    def setSources(self, sources: str):
        self.__sources = sources

    def getSourceLines(self):
        return self.__sources.split("\n")

    def __hash__(self) -> int:
        return hash(self.__filepath)

    def copy(self) -> CodeSource:
        return CodeSource(self.__filepath, self.__sources)
