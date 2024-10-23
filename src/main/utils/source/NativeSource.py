from dataclasses import dataclass
from os import PathLike

from utils.source.Source import Source, T


@dataclass(frozen=True)
class NativeSource(Source):
    __filepath: str
    __sources: bytes

    def getFilepath(self) -> T:
        return self.__filepath

    def writeToFile(self, path: T) -> None:
        with open(path, "wb") as f:
            f.write(self.__sources)
