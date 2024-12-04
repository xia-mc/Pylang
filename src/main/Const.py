from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Pylang import Pylang
    from transformers.TransManager import TransManager
    from log.Logger import Logger

pylang: Pylang
transManager: TransManager
logger: Logger

# TODO We should make them into the optimize config file
LOOP_UNFOLDING_MAX_LINES = 1000
