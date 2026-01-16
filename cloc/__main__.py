import argparse
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from time import time
from typing import Callable, Final, Optional, Sequence
from types import MappingProxyType

from cloc.argparser import initialize_parser, parse_arguments
from cloc.data_structures.config import ClocConfig
from cloc.parsing import parse_directory_verbose, parse_directory, parse_file
from cloc.utils import get_version
from cloc.utils import OUTPUT_MAPPING

def main(line: Sequence[str]) -> int:
    config: Final[ClocConfig] = ClocConfig.load_toml(Path(__file__).parent / "data_structures" / "config.toml")
    parser: Final[argparse.ArgumentParser] = initialize_parser(config)
    args: argparse.Namespace = parse_arguments(line, parser)

    if args.version:
        get_version()
        return 0

    is_file: bool = False

    if args.file:
        args.file = args.file[0]    # Fetch first (and only) entry from list since `nargs` param in parser.add_argument returns the args as a list
        is_file = True

    # Single file, no need to check and validate other default values
    if is_file:
        if not os.path.exists(args.file):
            raise FileNotFoundError(f"File {args.file} not found")
        if not os.path.isfile(args.file):
            raise ValueError(f"File argument {args.file} is not a valid file")
        
        singleline_symbol: Optional[bytes] = None
        multiline_start_symbol: Optional[bytes] = None
        multiline_end_symbol: Optional[bytes] = None

        # No symbols provided through the command line, consult languages metadata
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
                    multiline_start_symbol, multiline_end_symbol = comment_symbols

        else:
            if args.single_symbol:
                singleline_symbol = args.single_symbol[0].strip().encode()
            if args.multiline_symbol:
                pairing = args.multiline_symbol[0].strip().split(" ")
                if len(pairing) != 2:
                    raise ValueError(" ".join((f"Multiline symbols {args.multiline_symbol[0]} must",
                                               "be space-separated pair, such as '/* */'")))
                
                multiline_start_symbol = pairing[0].encode()
                multiline_end_symbol = pairing[1].encode()

        epoch: float = time()
        
        loc, total = parse_file(filepath=args.file, 
                               singleline_symbol=singleline_symbol, 
                               multiline_start_symbol=multiline_start_symbol, 
                               multiline_end_symbol=multiline_end_symbol, 
                               minChars=args.min_chars if isinstance(args.min_chars, int) else args.min_chars[0])
        outputMapping: MappingProxyType = MappingProxyType({"loc" : loc, "total" : total, "time" : f"{time()-epoch:.3f}s", "scanned at" : datetime.now().strftime("%d/%m/%y, at %H:%M:%S"), "platform" : platform.system()})
        if not args.output:
            print(outputMapping)
        else:
            outputFiletype: str = args.output[0].split(".")[-1].lower()

            # Fetch output function based on file extension, default to standard write logic
            outputFunction: Callable = OUTPUT_MAPPING.get(outputFiletype, OUTPUT_MAPPING[None])
            outputFunction(outputMapping=outputMapping, fpath=args.output[0])
        
        return 0

    # Directory
    args.dir = args.dir[0]  # Fetch first (and only) entry from list since `nargs` param in parser.add_argument returns the args as a list
    if not os.path.isdir(args.dir):
        raise NotADirectoryError(f"{args.dir} is not a valid directory")
    
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
    if args.verbose:
        outputMapping = parse_directory_verbose(dirData=root_data,
                                       customSymbols=symbol_data,
                                       fileFilterFunction=fileFilter,
                                       directoryFilterFunction=directoryFilter,
                                       minChars=args.min_chars if isinstance(args.min_chars, int) else args.min_chars[0],
                                       recurse=args.recurse)
        
        outputMapping["general"]["time"] = f"{time()-epoch:.3f}s"
        outputMapping["general"]["scanned at"] = datetime.now().strftime("%d/%m/%y, at %H:%M:%S")
        outputMapping["general"]["platform"] = platform.system()
    else:
        outputMapping = parse_directory(dirData=root_data,
                                                customSymbols=symbol_data,
                                                fileFilterFunction=fileFilter,
                                                directoryFilterFunction=directoryFilter,
                                                minChars=args.min_chars if isinstance(args.min_chars, int) else args.min_chars[0],
                                                recurse=args.recurse)
        
        outputMapping["general"]["time"] = f"{time()-epoch:.3f}s"
        outputMapping["general"]["scanned at"] = datetime.now().strftime("%d/%m/%y, at %H:%M:%S")
        outputMapping["general"]["platform"] = platform.system()

    print("=================== SCAN COMPLETE ====================")
    if args.output:
        outputFiletype: str = args.output[0].split(".")[-1].lower()

        # Fetch output function based on file extension, default to standard write logic
        outputFunction: Callable = OUTPUT_MAPPING.get(outputFiletype, OUTPUT_MAPPING[None])
        outputFunction(outputMapping=outputMapping, fpath=args.output[0])
    else:
        print(outputMapping)
    
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))