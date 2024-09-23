class Source:
    def __init__(self, filename: str, source: str):
        self.__filename: str = filename
        self.__sources: str = source

    def getFilename(self):
        return self.__filename

    def getSources(self):
        return self.__sources

    def getSourceLines(self):
        return self.__sources.split("\n")
