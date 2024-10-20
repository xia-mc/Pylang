import sys
import time
from typing import TextIO

import tqdm
import colorama
from colorama import Fore, Style

import Const
from log.LogLevel import LogLevel

# Initialize colorama
colorama.init(autoreset=True)


class Logger:
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    def __init__(self, level: LogLevel, file: TextIO | None = None):
        """
        Initialize the Logger with a log level and an optional output file.

        :param level: The minimum log level for messages to be logged.
        :param file: The file to which logs will be written. Defaults to stdout if None.
        """
        Const.logger = self
        self.level = level
        self.file = file

    def __del__(self):
        """
        Destructor to ensure the file is closed if it was opened.
        """
        if (self.file is not None) and (not self.file.closed):
            self.file.close()
            self.file = None

    def debug(self, *message: object) -> None:
        """
        Log a debug message.

        :param message: The message(s) to log.
        """
        self.log(LogLevel.DEBUG, *message)

    def info(self, *message: object) -> None:
        """
        Log an info message.

        :param message: The message(s) to log.
        """
        self.log(LogLevel.INFO, *message)

    def warn(self, *message: object) -> None:
        """
        Log a warning message.

        :param message: The message(s) to log.
        """
        self.log(LogLevel.WARN, *message)

    def error(self, *message: object) -> None:
        """
        Log an error message.

        :param message: The message(s) to log.
        """
        self.log(LogLevel.ERROR, *message)

    def critical(self, *message: object) -> None:
        """
        Log a critical message.

        :param message: The message(s) to log.
        """
        self.log(LogLevel.CRITICAL, *message)

    def log(self, level: LogLevel, *message: object) -> None:
        """
        Log a message at a specified log level with color.

        :param level: The log level of the message.
        :param message: The message(s) to log.
        """
        if level >= self.level:
            out = self._getOutput()
            timeStr = time.strftime("%H:%M:%S", time.localtime())

            # Select color based on log level
            color = self._getColor(level)

            with tqdm.tqdm.external_write_mode(file=None, nolock=True):
                out.write(f"{color}[{timeStr}] [{level.name}]: ")
                for msg in message:
                    out.write(str(msg))
                out.write(Style.RESET_ALL + "\n")

    def _getOutput(self) -> TextIO:
        """
        Get the output stream for logging.

        :return: The file object to which logs will be written, or stdout if no file is provided.
        """
        if self.file is not None:
            return self.file
        else:
            return sys.stdout

    @staticmethod
    def _getColor(level: LogLevel) -> str:
        """
        Get the color for the specified log level.

        :param level: The log level for which color is needed.
        :return: The color code as a string.
        """
        if level == LogLevel.DEBUG:
            return Fore.CYAN
        elif level == LogLevel.INFO:
            return Fore.GREEN
        elif level == LogLevel.WARN:
            return Fore.YELLOW
        elif level == LogLevel.ERROR:
            return Fore.RED
        elif level == LogLevel.CRITICAL:
            return Fore.MAGENTA
        else:
            return Fore.WHITE
