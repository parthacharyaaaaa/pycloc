from typing import Optional

__all__ = ("_parse_file_vm_map",
           "_parse_file",
           "_parse_file_no_chunk")

def _parse_file_vm_map(filename: str,
                     singleline_symbol: Optional[bytes] = None,
                     multiline_start_symbol: Optional[bytes] = None,
                     multiline_end_symbol: Optional[bytes] = None,
                     minimum_characters: int = 0,
                     /) -> tuple[int, int]: ...

def _parse_file(filename: str,
                singleline_symbol: Optional[bytes] = None,
                multiline_start_symbol: Optional[bytes] = None,
                multiline_end_symbol: Optional[bytes] = None,
                minimum_characters: int = 0,
                /) -> tuple[int, int]: ...

def _parse_file_no_chunk(filename: str,
                         singleline_symbol: Optional[bytes] = None,
                         multiline_start_symbol: Optional[bytes] = None,
                         multiline_end_symbol: Optional[bytes] = None,
                         minimum_characters: int = 0,
                         /) -> tuple[int, int]: ...
