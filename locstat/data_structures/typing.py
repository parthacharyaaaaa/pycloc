import os
from typing import Any, Literal, Optional, Protocol, TypeAlias, TypeVar, Union

__all__ = ("LanguageMetadata",
           "OutputFunction",
           "SupportsBuffer",
           "FileParsingFunction",
           "SupportsMembershipChecks")

LanguageMetadata: TypeAlias = tuple[Optional[bytes], Optional[bytes], Optional[bytes]]

class OutputFunction(Protocol):
    def __call__(self,
                 output_mapping: dict[str, Any],
                 filepath: Union[str, os.PathLike[str], int]) -> None:
        ...

class SupportsBuffer(Protocol):
    def __buffer__(self, flags: int, /) -> memoryview: ...

    # def __release_buffer__(self, buffer: memoryview) -> None: ...

class FileParsingFunction(Protocol):
    def __call__(self,
                 filepath: str,
                 singleline_symbol: Optional[bytes] = None,
                 multiline_start_symbol: Optional[bytes] = None,
                 multiline_end_symbol: Optional[bytes] = None,
                 minimum_characters: int = 0,
                 /) -> tuple[int, int]: ...

T = TypeVar("T", covariant=True)
class SupportsMembershipChecks(Protocol[T]):
    def __contains__(self, o: object, /) -> bool: ...