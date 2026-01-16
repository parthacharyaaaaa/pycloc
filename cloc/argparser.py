import argparse
from typing import Final, Sequence

from cloc.data_structures.config import ClocConfig
from cloc.utilities.presentation import OUTPUT_MAPPING, dump_std_output

__all__ = ("initialize_parser", "parse_arguments")

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
                        nargs=1,
                        help="Specify the directory to scan. Either this or '-f' must be used")

    target_group.add_argument("-f", "--file",
                        nargs=1,
                        help="Specify the file to scan. Either this or '-d' must be used")

    # Parsing logic manipulation
    parser.add_argument("-mc", "--min-chars",
                        nargs=1,
                        type=int,
                        help=" ".join(("Specify the minimum number of non-whitespace characters a line",
                                    "should have to be considered an LOC")),
                        default=config.minimum_characters)

    parser.add_argument("-ss", "--single-symbol",
                        nargs=1,
                        help=" ".join(("Specify the single-line comment symbol.",
                                    "By default, the comments are identified via file extension itself,",
                                    "Note that if this flag is specified with the directory flag,",
                                    "then all files within that directory are",
                                    "checked against this comment symbol")))

    parser.add_argument("-ms", "--multiline-symbol",
                        nargs=1,
                        help=" ".join(("Specify the multi-line comment symbols as a",
                                    "space-separated pair of opening and closing symbols.",
                                    "Behaves similiar to single-line comments")))

    # Directory parsing logic
    parser.add_argument("-r", "--recurse",
                        help="Recursively scan every sub-directory too",
                        action="store_true",
                        default=config.recurse)

    parser.add_argument("-xf", "--exclude-file",
                        nargs="+",
                        help="Exclude files by name")

    parser.add_argument("-xd", "--exclude-dir",
                        nargs="+",
                        help="Exclude directories by name")

    parser.add_argument("-xt", "--exclude-type",
                        nargs="+",
                        help="Exclude files by extension")

    parser.add_argument("-id", "--include-dir",
                        nargs="+",
                        help="Include directories by name")

    parser.add_argument("-if", "--include-file",
                        nargs="+",
                        help="Include files by name")

    parser.add_argument("-it", "--include-type",
                        nargs="+",
                        help=" ".join(("Include files by extension, useful for specificity",
                                       "when working with directories with files for different languages")))

    # Output control
    parser.add_argument("-vb", "--verbose",
                        help="Get LOC and total lines for every file scanned",
                        action="store_true",
                        default=config.verbose)

    parser.add_argument("-o", "--output",
                        nargs=1,
                        help=" ".join(("Specify output file to dump counts into.",
                                    "If not specified, output is dumped to stdout.",
                                    "If output file is in",
                                    f"{', '.join(k for k,v in OUTPUT_MAPPING.items() if v != dump_std_output)}",
                                    "then output is formatted differently.")))

    return parser

def parse_arguments(line: Sequence[str],
                    parser: argparse.ArgumentParser) -> argparse.Namespace:
    parsed_arguments: argparse.Namespace = parser.parse_args(line)
    
    # Additional validation rules not covered in parse_args
    inclusion_provided: bool = bool(parsed_arguments.include_dir or parsed_arguments.include_file)
    if inclusion_provided and (parsed_arguments.exclude_dir or parsed_arguments.exclude_file):
        raise ValueError("Only one of inclusion (-it, -if) or exclusion (-xf, xt) can be specified, but not both")
    
    return parsed_arguments