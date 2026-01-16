'''Helper functions'''
import orjson
from typing import Mapping, Optional, Union

from cloc.config import LANGUAGES, WORKING_DIRECTORY

def get_version():
    with open(WORKING_DIRECTORY / "config.json") as config:
        version: str = orjson.loads(config.read()).get("version")
        if not version:
            print("py-cloc: version not found!")
        else:
            print(f"py-cloc {version}")

def find_comment_symbols(extension: str,
                       symbolMapping: Union[Mapping[str, Mapping[str, str]], None] = None
                       ) -> Union[bytes, tuple[bytes, bytes], tuple[bytes, tuple[bytes, bytes]]]:
        '''### Find symbols that denote a comment for a specific language
        
        #### args
        extension: File extension of the language\n
        symbolMapping: Mapping of file extensions and their corresponding symbols. Keys are `symbols` for single-line comments and `multilined` for multi-line comments. See `languages.json` for the actual mapping'''

        extension = extension.strip().lower()
        if not symbolMapping:
            symbolMapping = LANGUAGES

        singleline_symbol: Optional[str] = symbolMapping["symbols"].get(extension)
        multiline_symbols: Optional[str] = symbolMapping["multilined"].get(extension)
        multiline_symbol_pair: Optional[list[str]] = None

        if not (singleline_symbol or multiline_symbols):
            raise ValueError(f"No comment symbols found for extension .{extension}")
        
        if multiline_symbols:
            multiline_symbol_pair = multiline_symbols.split()
            if not len(multiline_symbol_pair) == 2:
                raise ValueError(f"Invalid syntax for multiline comments for extension: .{extension}")
        
        if not singleline_symbol:
            assert multiline_symbol_pair
            return multiline_symbol_pair[0].encode(), multiline_symbol_pair[1].encode()
        if not multiline_symbol_pair:
            return singleline_symbol.encode()
        
        return (singleline_symbol.encode(),
                (multiline_symbol_pair[0].encode(), multiline_symbol_pair[1].encode()))
