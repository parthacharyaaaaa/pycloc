from typing import Optional

__all__ = ("_parse_memoryview",)

def _parse_memoryview(mapped_space: memoryview[int],
                      singleline_symbol: Optional[bytes] = None,
                      multiline_start_symbol: Optional[bytes] = None,
                      multiline_end_symbol: Optional[bytes] = None,
                      minimum_characters: int = 0
                      ) -> tuple[int, int]: ...