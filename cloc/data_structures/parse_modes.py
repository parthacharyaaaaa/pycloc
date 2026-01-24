from enum import StrEnum

__all__ = ("ParseMode",)

class ParseMode(StrEnum):
    MMAP = "MMAP"
    BUFFERED = "BUF"
    COMPLETE = "COMP"