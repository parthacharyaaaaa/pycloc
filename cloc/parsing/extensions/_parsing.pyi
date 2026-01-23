from typing import Optional
from cloc.data_structures.typing import SupportsBuffer

__all__ = ("_parse_buffer",)

def _parse_buffer(mapped_space: SupportsBuffer,
                      singleline_symbol: Optional[bytes] = None,
                      multiline_start_symbol: Optional[bytes] = None,
                      multiline_end_symbol: Optional[bytes] = None,
                      minimum_characters: int = 0
                      ) -> tuple[int, int]: ...