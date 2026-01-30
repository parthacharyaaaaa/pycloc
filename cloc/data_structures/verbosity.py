from enum import StrEnum

__all__ = ("Verbosity",)

class Verbosity(StrEnum):
    BARE = "BARE"
    REPORT = "REPORT"
    DETAILED = "DETAILED"