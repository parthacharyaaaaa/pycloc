import argparse
import os
import sys
from typing import Final, Sequence

from cloc.data_structures.config import ClocConfig
from cloc.data_structures.parse_modes import ParseMode
from cloc.data_structures.verbosity import Verbosity
from cloc.utilities.presentation import OUTPUT_MAPPING, dump_std_output

__all__ = ("initialize_parser", "parse_arguments")

def _validate_directory(arg: str) -> str:
    arg = arg.strip()
    if not os.path.isdir(arg):
        sys.stderr.write(f"Directory {arg} could not be found\n")
        sys.exit(1)
    return arg

def _validate_filepath(arg: str) -> str:
    arg = arg.strip()
    if not os.path.isfile(arg):
        sys.stderr.write(f"File {arg} could not be found\n")
        sys.exit(1)
    return arg

def _validate_min_chars(arg: str) -> int:
    min_chars: int = int(arg)
    if min_chars < 0:
        sys.stderr.write("Minimum characters cannot be negative\n")
        sys.exit(1)
    elif min_chars == 0:
        sys.stdout.write("Note: minimum characters of 0 implies empty lines also contribute to LOC\n")
    return min_chars

def _validate_parsing_mode(arg: str) -> ParseMode:
    arg = arg.strip().upper()
    try:
        return ParseMode(arg)
    except ValueError:
        sys.stderr.write(f"Invalid parsing mode {arg}, supported parsing modes: {", ".join((k for k in ParseMode._value2member_map_.keys()))}\n")
        sys.exit(1)

def _validate_max_depth(arg: str) -> int:
    try:
        depth: int = int(arg)
    except ValueError:
        sys.stderr.write("Traversal depth must be integer value\n")
        sys.exit(1)
    return depth

def _validate_verbosity(arg: str) -> Verbosity:
    arg = arg.strip().upper()
    try:
        return Verbosity(arg)
    except ValueError:
        sys.stderr.write(" ".join((f"Invalid verbosity mode {arg},",
                                   "Supported:",
                                   ', '.join((k for k in Verbosity._value2member_map_)),
                                   "\n")))
        sys.exit(1)

def initialize_parser(config: ClocConfig) -> argparse.ArgumentParser:
    '''Instantiate and return an argument parser

    :param config: Configuration instance used to add additional validation/parsing rules
    :type config: ClocConfig
    
    :return: argparse.ArgumentParser'''

    parser: Final[argparse.ArgumentParser] = argparse.ArgumentParser(prog="pycloc",
                                                                     description="CLI tool to count lines of code")
    # Tool identification
    parser.add_argument("-v", "--version",
                        help="Current version of cloc",
                        action="store_true")

    # Target
    target_group: argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("-d", "--dir",
                        type=_validate_directory,
                        help="Specify the directory to scan. Either this or '-f' must be used")

    target_group.add_argument("-f", "--file",
                        type=_validate_filepath,
                        help="Specify the file to scan. Either this or '-d' must be used")

    # Parsing logic manipulation
    parser.add_argument("-mc", "--min-chars",
                        type=_validate_min_chars,
                        help=" ".join(("Specify the minimum number of non-whitespace characters a line",
                                    "should have to be considered an LOC")),
                        default=config.minimum_characters)
    
    # Directory parsing logic
    parser.add_argument("-md", "--max-depth",
                        help=" ".join(("Recursively scan sub-directories upto the given level",
                                       "Negative values are treated as infinite depth")),
                        type=_validate_max_depth,
                        default=0)

    file_filter_group: argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group()

    file_filter_group.add_argument("-xf", "--exclude-file",
                                   nargs="+",
                                   help="Exclude files by name")
    
    file_filter_group.add_argument("-if", "--include-file",
                                   nargs="+",
                                   help="Include files by name")

    dir_filter_group: argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group()

    dir_filter_group.add_argument("-xd", "--exclude-dir",
                                  nargs="+",
                                  help="Exclude directories by name")

    dir_filter_group.add_argument("-id", "--include-dir",
                                  nargs="+",
                                  help="Include directories by name")

    type_filter_group: argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group()
    type_filter_group.add_argument("-xt", "--exclude-type",
                        nargs="+",
                        help="Exclude files by extension")

    type_filter_group.add_argument("-it", "--include-type",
                        nargs="+",
                        help=" ".join(("Include files by extension, useful for specificity",
                                       "when working with directories with files for different languages")))

    # Output control
    parser.add_argument("-vb", "--verbosity",
                        type=_validate_verbosity,
                        help=" ".join(("Determine amount of details reported.",
                                        "Available:",
                                        ", ".join(k for k in Verbosity._value2member_map_))),
                        default=config.verbosity)

    parser.add_argument("-o", "--output",
                        help=" ".join(("Specify output file to dump counts into.",
                                    "If not specified, output is dumped to stdout.",
                                    "If output file is in",
                                    f"{', '.join(k for k,v in OUTPUT_MAPPING.items() if v != dump_std_output)}",
                                    "then output is formatted differently.")))
    
    parser.add_argument("-pm", "--parsing-mode",
                        type=_validate_parsing_mode,
                        default=ParseMode.BUFFERED,
                        help=" ".join(("Override default file parsing behaviour.",
                                       "Available options:",
                                       ', '.join(ParseMode._value2member_map_.keys()))),)

    return parser

def parse_arguments(line: Sequence[str],
                    parser: argparse.ArgumentParser) -> argparse.Namespace:
    parsed_arguments: argparse.Namespace = parser.parse_args(line)
    
    # Additional validation rules not covered in parse_args
    # TODO: Add additional mutual exclusion logic

    return parsed_arguments