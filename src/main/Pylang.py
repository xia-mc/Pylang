from __future__ import annotations

import os
import sys

import Const
from log.LogLevel import LogLevel
from log.Logger import Logger
from transformers.OptimizeLevel import OptimizeLevel
from transformers.TransManager import TransManager


class Pylang:
    def __init__(self):
        Const.pylang = self
        self.manager: TransManager | None = None
        self.logger: Logger | None = None

    def main(self, *args: str):
        level = OptimizeLevel.O1
        logLevel = LogLevel.INFO
        logToFile = False
        filenames: list[str] = []
        outputPath: str = r".\out"

        try:
            index = 0
            while index < len(args):
                arg = args[index].lower()
                match arg:
                    case "-o0":
                        level = OptimizeLevel.O0
                    case "-o1":
                        level = OptimizeLevel.O1
                    case "-o2":
                        level = OptimizeLevel.O2
                    case "-o3":
                        level = OptimizeLevel.O3
                    case "-critical":
                        logLevel = LogLevel.CRITICAL
                    case "-error":
                        logLevel = LogLevel.ERROR
                    case "-warn":
                        logLevel = LogLevel.WARN
                    case "-info":
                        logLevel = LogLevel.INFO
                    case "-debug":
                        logLevel = LogLevel.DEBUG
                    case "-tofile":
                        logToFile = True
                    case "-f":
                        filenames.append(args[index + 1])
                        index += 1
                    case "-d":
                        for root, dirs, files in os.walk(args[index + 1]):
                            for file in files:
                                filenames.append(os.path.join(root, file))
                        index += 1
                    case "-o":
                        outputPath = args[index + 1]
                        index += 1
                index += 1
        except IndexError:
            pass
        except Exception as e:
            print("Exception during parse args.")
            print(e)
            exit(1)

        self.logger = Logger(logLevel, open("latest.log", "w") if logToFile else None)
        self.manager = TransManager(self, self.logger, level)
        self.manager.register()

        self.logger.debug("Start parsing files.")
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            self.manager.parse(filename)
        self.logger.info(f"Parsed {len(self.manager.sources)} files.")

        output = self.manager.transform()
        for source in output:
            path = outputPath + source.getFilename()
            self.logger.debug(f"Write to {path}")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as file:
                file.write(source.getSources())
        input("Press Enter to continue...")


if __name__ == "__main__":
    pylang = Pylang()
    pylang.main(*sys.argv[1::])
