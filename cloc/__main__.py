import argparse
import os
import platform
import sys
import time
from array import array
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Final, Literal, MutableMapping, Optional, Sequence, Union

from cloc.argparser import initialize_parser, parse_arguments
from cloc.data_structures.config import ClocConfig
from cloc.utilities.presentation import OUTPUT_MAPPING, OutputFunction, dump_std_output
from cloc.parsing import parse_directory_verbose, parse_directory, parse_file
from cloc.data_structures.typing import OutputMapping

def main(line: Sequence[str]) -> int:
    config: Final[ClocConfig] = ClocConfig.load_toml(Path(__file__).parent / "config.toml")
    parser: Final[argparse.ArgumentParser] = initialize_parser(config)
    args: argparse.Namespace = parse_arguments(line, parser)

    output_mapping: Optional[OutputMapping] = None

    singleline_symbol: Optional[bytes] = None
    multiline_start_symbol: Optional[bytes] = None
    multiline_end_symbol: Optional[bytes] = None

    # Symbols provided through the command line, consult languages metadata
    if args.single_symbol:
        singleline_symbol = args.single_symbol[0].strip().encode()
    if args.multiline_symbol:
        pairing = args.multiline_symbol[0].strip().split(" ")
        if len(pairing) != 2:
            raise ValueError(" ".join((f"Multiline symbols {args.multiline_symbol[0]} must",
                                        "be space-separated pair, such as '/* */'")))
        
        multiline_start_symbol = pairing[0].encode()
        multiline_end_symbol = pairing[1].encode()
    
    # Single file, no need to check and validate other default values
    if args.file:
        if not(args.single_symbol and args.multilline_symbol):
            comment_symbols = config.find_comment_symbol(args.file.split(".")[-1])

            # Single-line comment symbol only
            if isinstance(comment_symbols, bytes):
                singleline_symbol = comment_symbols
            elif isinstance(comment_symbols, tuple):
                if isinstance(comment_symbols[1], tuple):
                    # Both single-line and multi-line symbols
                    singleline_symbol = comment_symbols[0]
                    multiline_start_symbol, multiline_end_symbol = comment_symbols[1]
                else:
                    # Multi-line symbols only
                    multiline_start_symbol, multiline_end_symbol = comment_symbols  # type: ignore
        
        epoch: float = time.time()
        loc, total = parse_file(filepath=args.file, 
                                singleline_symbol=singleline_symbol, 
                                multiline_start_symbol=multiline_start_symbol, 
                                multiline_end_symbol=multiline_end_symbol, 
                                minimum_characters=args.min_chars)
        
        output_mapping = {"loc" : loc,
                          "total" : total,
                          "time" : f"{time.time()-epoch:.3f}s",
                          "scanned at" : datetime.now().strftime("%d/%m/%y, at %H:%M:%S"),
                          "platform" : platform.system()}
        
    else:
        symbol_data: Optional[dict[str, bytes]] = {}
        if singleline_symbol:
            symbol_data['singleline'] = singleline_symbol
        if multiline_start_symbol:
            assert multiline_end_symbol
            symbol_data['multistart'] = multiline_start_symbol
            symbol_data['multiend'] = multiline_end_symbol

        # Either inclusion or exclusion can be specified, but not both
        inclusion_applied: bool = bool(args.include_type or args.include_file)
        file_filter_applied = bool(inclusion_applied or (args.exclude_file or args.exclude_type)) 

        # Can use short circuit now since we are sure that only inclusion or exclusion has been specified
        extensions: list[str] = args.exclude_type or args.include_type or []
        files: list[str] = args.exclude_file or args.include_file or []

        extensionSet: frozenset[str] = frozenset(extension for extension in extensions)
        fileSet: frozenset[str] = frozenset(file for file in files)

        # Function for determining valid files
        if file_filter_applied:
            file_filter: Callable[[str], bool] = lambda file: ((file.split(".")[-1] in extensionSet
                                                                or file in fileSet)
                                                               if inclusion_applied else
                                                               (file.split(".")[-1] not in extensionSet
                                                                and file not in fileSet))
        else:
            file_filter = lambda _ : True    # No file filter logic given, return True always
        
        if bool(args.include_dir or args.exclude_dir):
            directory_set: frozenset[str] = frozenset(directory for directory in args.include_dir or args.exclude_dir)
            directory_filter: Callable[[str], bool] = lambda dir : (dir in directory_set if inclusion_applied
                                                                    else dir not in directory_set)
        else:
            # No directory filters given, accept subdirectories based on recurse flag
            directory_filter = lambda _ : bool(args.recurse)

        root: str = os.path.abspath(args.dir)
        root_data = os.scandir(root)

        kwargs: dict[str, Any] = {"directory_data" : root_data,
                                  "config" : config,
                                  "file_filter_function" : file_filter,
                                  "directory_filter_function" : directory_filter,
                                  "minimum_characters" : args.min_chars,
                                  "recurse" : args.recurse}
        
        epoch: float = time.time()
        if args.verbose:
            output_mapping = parse_directory_verbose(**kwargs)
        else:
            line_data: array[int] = array("L", (0, 0))
            parse_directory(**kwargs, line_data=line_data)
            output_mapping = {"general" : {"total" : line_data[0], "loc" : line_data[1]}}
        
        assert isinstance(output_mapping["general"], MutableMapping)
        output_mapping["general"]["time"] = f"{time.time()-epoch:.3f}s"
        output_mapping["general"]["scanned at"] = datetime.now().strftime("%d/%m/%y, at %H:%M:%S")
        output_mapping["general"]["platform"] = platform.system()

    # Emit results
    output_file: Union[int, str] = sys.stdout.fileno()
    output_handler: OutputFunction = dump_std_output
    mode: Literal["w+", "a"] = "a"
    if args.output:
        output_file = args.output[0].strip().lower()
        assert isinstance(output_file, str)
        output_extension: str = output_file.split(".")[-1]
        mode = "w+"
        # Fetch output function based on file extension, default to standard write logic
        output_handler = OUTPUT_MAPPING.get(output_extension, output_handler)
    
    print("=================== SCAN COMPLETE ====================")
    output_handler(output_mapping=output_mapping, filepath=output_file, mode=mode)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))