import argparse
import os
import platform
import sys
import time
from array import array
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Final, Literal, Optional, Union

from cloc.argparser import initialize_parser, parse_arguments
from cloc.data_structures.config import ClocConfig
from cloc.data_structures.typing import (FileParsingFunction,
                                         OutputMapping)
from cloc.data_structures.verbosity import Verbosity
from cloc.parsing.directory import (parse_directory,
                                    parse_directory_record,
                                    parse_directory_verbose)
from cloc.utilities.core import (construct_file_filter,
                                 derive_file_parser)
from cloc.utilities.presentation import (OUTPUT_MAPPING,
                                         OutputFunction,
                                         dump_std_output)

__all__ = ("main",)

def main() -> int:
    config: Final[ClocConfig] = ClocConfig.load_toml(Path(__file__).parent / "config.toml")
    parser: Final[argparse.ArgumentParser] = initialize_parser(config)
    args: argparse.Namespace = parse_arguments(sys.argv[1:], parser)

    output_mapping: Optional[OutputMapping] = None

    singleline_symbol: Optional[bytes] = None
    multiline_start_symbol: Optional[bytes] = None
    multiline_end_symbol: Optional[bytes] = None

    # Symbols provided through the command line, consult languages metadata
    if args.single_symbol:
        singleline_symbol = args.single_symbol.strip().encode()
    if args.multiline_symbol:
        pairing = args.multiline_symbol.strip().split(" ")
        if len(pairing) != 2:
            raise ValueError(" ".join((f"Multiline symbols {args.multiline_symbol[0]} must",
                                        "be space-separated pair, such as '/* */'")))
        
        multiline_start_symbol = pairing[0].encode()
        multiline_end_symbol = pairing[1].encode()
    
    file_parser_function: Final[FileParsingFunction] = derive_file_parser(args.parsing_mode)
    # Single file, no need to check and validate other default values
    if args.file:
        if not(args.single_symbol and args.multilline_symbol):
            singleline_symbol, multiline_start_symbol, multiline_end_symbol = config.symbol_mapping.get(args.file.rsplit(".", 1)[-1],
                                                                                                        (None, None, None))
        epoch: float = time.time()
        total, loc = file_parser_function(args.file, 
                                          singleline_symbol, 
                                          multiline_start_symbol, 
                                          multiline_end_symbol, 
                                          args.min_chars)
        
        output_mapping = {"loc" : loc,
                          "total" : total,
                          "time" : f"{time.time()-epoch:.3f}s",
                          "scanned at" : datetime.now().strftime("%d/%m/%y, at %H:%M:%S"),
                          "platform" : platform.system()}
        
    else:
        extension_set: frozenset[str] = frozenset(extension for extension in
                                                 (args.exclude_type or args.include_type or []))
        file_set: frozenset[str] = frozenset(file for file in
                                            (args.exclude_file or args.include_file or []))

        # Constructing file filter
        file_filter: Callable[[str], bool] = construct_file_filter(extension_set, file_set,
                                                                   bool(args.include_file),
                                                                   bool(args.exclude_file),
                                                                   bool(args.include_type),
                                                                   bool(args.exclude_type))
        
        directory_filter: Callable[[str], bool] = lambda directory : True
        if (args.include_dir or args.exclude_dir):
            directory_set: frozenset[str] = frozenset(directory for directory in
                                                      (args.include_dir or args.exclude_dir))
            directory_filter: Callable[[str], bool] = lambda directory : (directory in directory_set
                                                                          if args.include_dir
                                                                          else directory not in directory_set)

        kwargs: dict[str, Any] = {"directory_data" : os.scandir(os.path.abspath(args.dir)),
                                  "config" : config,
                                  "file_parsing_function" : file_parser_function,
                                  "file_filter_function" : file_filter,
                                  "directory_filter_function" : directory_filter,
                                  "minimum_characters" : args.min_chars,
                                  "depth" : args.max_depth}
        output_mapping = {}
        epoch: float = time.time()
        if args.verbosity == Verbosity.BARE:
            line_data: array[int] = array("L", (0, 0))
            parse_directory(**kwargs, line_data=line_data)
            output_mapping["general"] = ({"total" : line_data[0],
                                          "loc" : line_data[1]})
        else:
            language_record: dict[str, dict[str, int]] = {}
            kwargs.update({"language_record" : language_record})

            if args.verbosity == Verbosity.DETAILED:
                output_mapping.update(parse_directory_verbose(**kwargs))
                total, loc = output_mapping.pop("total"), output_mapping.pop("loc")
                output_mapping["general"] = {"total" : total,
                                            "loc" : loc}
            else:
                line_data: array[int] = array("L", (0, 0))
                parse_directory_record(**kwargs, line_data=line_data)
                output_mapping["general"] = ({"total" : line_data[0],
                                              "loc" : line_data[1]})
            
            output_mapping["languages"] = language_record
        
        output_mapping["general"].update({"time" : f"{time.time()-epoch:.3f}s",
                                          "scanned_at" : datetime.now().strftime("%d/%m/%y, at %H:%M:%S"),
                                          "platform" : platform.system()})
        
    # Emit results
    output_file: Union[int, str] = sys.stdout.fileno()
    output_handler: OutputFunction = dump_std_output
    mode: Literal["w+", "a"] = "a"
    if args.output:
        assert isinstance(args.output, str)
        output_file = args.output.strip()
        output_extension: str = output_file.split(".")[-1]
        mode = "w+"
        # Fetch output function based on file extension, default to standard write logic
        output_handler = OUTPUT_MAPPING.get(output_extension, output_handler)
    
    print("=================== SCAN COMPLETE ====================")
    output_handler(output_mapping=output_mapping, filepath=output_file, mode=mode)
    return 0

if __name__ == "__main__":
    sys.exit(main())