from dataclasses import dataclass

from utils.source.Source import Source


@dataclass(frozen=True)
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

    def getSourceLines(self):
        return self.__sources.split("\n")
