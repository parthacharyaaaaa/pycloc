'''Data structures used within the locstat package'''

from locstat.data_structures.exceptions import (ExitException,
                                             InvalidConfigurationException)
from locstat.data_structures.singleton import SingletonMeta
from locstat.data_structures.parse_modes import ParseMode
from locstat.data_structures.config import ClocConfig
import locstat.data_structures.typing as cloc_typing
from locstat.data_structures.verbosity import Verbosity

__all__ = ("ExitException",
           "InvalidConfigurationException",
           "SingletonMeta",
           "ParseMode",
           "ClocConfig",
           "cloc_typing",
           "Verbosity")