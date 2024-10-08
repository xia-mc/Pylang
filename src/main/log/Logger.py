from __future__ import annotations

import sys
import time
from typing import TextIO

import Const
from log.LogLevel import LogLevel


class Logger:
    def __init__(self, level: LogLevel, file: TextIO | None = None):
        Const.logger = self
        self.level = level
        self.file = file

    def __del__(self):
        if (self.file is not None) and (not self.file.closed):
            self.file.close()
            self.file = None

    def debug(self, *message: object):
        self.log(LogLevel.DEBUG, *message)

    def info(self, *message: object):
        self.log(LogLevel.INFO, *message)

    def warn(self, *message: object):
        self.log(LogLevel.WARN, *message)

    def error(self, *message: object):
        self.log(LogLevel.ERROR, *message)

    def critical(self, *message: object):
        self.log(LogLevel.CRITICAL, *message)

    def log(self, level: LogLevel, *message: object):
        if level >= self.level:
            out = self._getOutput()
            timeStr = time.strftime("%H:%M:%S", time.gmtime())
            out.write(f"[{timeStr}] [{level.name}]: ")
            for msg in message:
                out.write(str(msg))
            out.write("\n")
            out.flush()

    def _getOutput(self) -> TextIO:
        if self.file is not None:
            return self.file
        else:
            return sys.stdout
