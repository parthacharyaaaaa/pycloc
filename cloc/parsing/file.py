from typing import Optional
import mmap

from cloc.parsing.extensions._parsing import _parse_memoryview

__all__ = ("parse_file",)

def parse_file(filepath: str,
                singleline_symbol: Optional[bytes] = None,
                multiline_start_symbol: Optional[bytes] = None,
                multiline_end_symbol: Optional[bytes] = None,
                minimum_characters: int = 0) -> tuple[int, int]:
    with open(filepath, 'rb') as file:
        try:
            mapped_file = mmap.mmap(file.fileno(), 0, flags=mmap.MAP_PRIVATE)
            mapped_file.madvise(mmap.MADV_SEQUENTIAL)
        except ValueError:
            return 0, 0
        with mapped_file:
            return _parse_memoryview(memoryview(mapped_file),
                                    singleline_symbol,
                                    multiline_start_symbol,
                                    multiline_end_symbol,
                                    minimum_characters)