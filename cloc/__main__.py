import argparse
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from time import time
from typing import Any, Final, MutableMapping, Optional, Sequence, Union

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
        
        epoch: float = time()
        loc, total = parse_file(filepath=args.file, 
                                singleline_symbol=singleline_symbol, 
                                multiline_start_symbol=multiline_start_symbol, 
                                multiline_end_symbol=multiline_end_symbol, 
                                minimum_characters=args.min_chars)
        
        output_mapping = {"loc" : loc,
                          "total" : total,
                          "time" : f"{time()-epoch:.3f}s",
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
        
        ### Handle file-level filtering logic, if any ###
        bFileFilter: bool = False

        # Either inclusion or exclusion can be specified, but not both
        bInclusion: bool = bool(args.include_type or args.include_file)
        if bInclusion or (args.exclude_file or args.exclude_type):
            bFileFilter = True

        # Can use short circuit now since we are sure that only inclusion or exclusion has been specified
        extensions: list[str] = args.exclude_type or args.include_type or []
        files: list[str] = args.exclude_file or args.include_file or []
        dirs : list[str] = args.exclude_dir or args.include_dir or []

        # Casting to set for faster lookups
        extensionSet: frozenset = frozenset(extension for extension in extensions)
        fileSet: frozenset = frozenset(file for file in files)

        # Function for determining valid files
        if bFileFilter:
            fileFilter = lambda file: (file.split(".")[-1] in extensionSet or file in fileSet) if bInclusion else (file.split(".")[-1] not in extensionSet and file not in fileSet)
        else:
            fileFilter = lambda _ : True    # No file filter logic given, return True blindly
        
        ### Handle direcotory-level filtering logic, if any ###
        bDirFilter: bool = args.include_dir or args.exclude_dir

        if bDirFilter:
            bDirInclusion: bool = False
            directories: set = set()
            
            if args.include_dir:
                directories = set(args.include_dir)
                bDirInclusion = True
            directories = set(args.exclude_dir)

            # Cast for faster lookups
            dirSet: frozenset = frozenset(dir for dir in directories)
            
            directoryFilter = lambda dir : dir in dirSet if bInclusion else dir not in dirSet
        else:
            directoryFilter = lambda _ : False if not args.recurse else True          # No directory filters given, accept subdirectories based on recurse flag

        root: os.PathLike = os.path.abspath(args.dir)
        root_data = os.walk(root)

        epoch = time()
        kwargs: dict[str, Any] = {"directory_data" : root_data,
                                  "config" : config,
                                  "custom_symbols" : symbol_data,
                                  "file_filter_function" : fileFilter,
                                  "directory_filter_function" : directoryFilter,
                                  "minimum_characters" : args.min_chars,
                                  "recurse" : args.recurse}
        
        output_mapping = parse_directory_verbose(**kwargs) if args.verbose else parse_directory(**kwargs)
        
        assert isinstance(output_mapping["general"], MutableMapping)
        output_mapping["general"]["time"] = f"{time()-epoch:.3f}s"
        output_mapping["general"]["scanned at"] = datetime.now().strftime("%d/%m/%y, at %H:%M:%S")
        output_mapping["general"]["platform"] = platform.system()

    # Emit results
    output_file: Union[int, str] = sys.stdout.fileno()
    output_handler: OutputFunction = dump_std_output
    if args.output:
        output_file = args.output[0].strip().lower()
        assert isinstance(output_file, str)
        output_extension: str = output_file.split(".")[-1]

        # Fetch output function based on file extension, default to standard write logic
        output_handler = OUTPUT_MAPPING.get(output_extension, output_handler)
    
    print("=================== SCAN COMPLETE ====================")
    output_handler(output_mapping=output_mapping, filepath=args.output[0])
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))