import argparse
import os
import platform
import sys
import time
from array import array
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Final, Literal, NoReturn, Union

from cloc.argparser import initialize_parser, parse_arguments
from cloc import __version__, __tool_name__
from cloc.data_structures.config import ClocConfig
from cloc.data_structures.typing import FileParsingFunction, LanguageMetadata
from cloc.data_structures.verbosity import Verbosity
from cloc.parsing.directory import (parse_directory,
                                    parse_directory_record,
                                    parse_directory_verbose)
from cloc.utilities.core import (construct_directory_filter, construct_file_filter,
                                 derive_file_parser)
from cloc.utilities.presentation import (OUTPUT_MAPPING,
                                         OutputFunction,
                                         dump_std_output)

__all__ = ("main",)

def main() -> int:
    config: Final[ClocConfig] = ClocConfig.load_toml(Path(__file__).parent / "config.toml")
    parser: Final[argparse.ArgumentParser] = initialize_parser(config)
    args: argparse.Namespace = parse_arguments(sys.argv[1:], parser)

    if args.version:
        print(f"{__tool_name__} {__version__}")
        return 0

    # Because of nargs="*" in argparser's config argument,
    # the only way to determine whether --config was passed
    # is by negation of remaining args in the same mutually exclusive group 
    if not (args.file or args.dir):
        if not args.config: # View current configurations
            print(config.configurations_string)
            return 0
        
        for (key, value) in (args.config):    # items in pairs
            config.update_configuration(key, value)
        return 0

    output_mapping: dict[str, Any] = {}
    
    file_parser_function: Final[FileParsingFunction] = derive_file_parser(args.parsing_mode)
    # Single file, no need to check and validate other default values
    if args.file:
        comment_data: LanguageMetadata = config.symbol_mapping.get(args.file.rsplit(".", 1)[-1],
                                                                   (None, None, None))
        singleline_symbol, multiline_start_symbol, multiline_end_symbol = comment_data
        epoch: float = time.time()
        total, loc = file_parser_function(args.file, 
                                          singleline_symbol, 
                                          multiline_start_symbol, 
                                          multiline_end_symbol, 
                                          args.min_chars)
        
        output_mapping["general"] = {"loc" : loc, "total" : total}
        
    else:
        extension_set: frozenset[str] = frozenset(extension for extension in
                                                 (args.exclude_type or args.include_type or []))
        file_set: frozenset[str] = frozenset(file for file in
                                            (args.exclude_file or args.include_file or []))

        file_filter: Callable[[str, str], bool] = construct_file_filter(extension_set, file_set,
                                                                        bool(args.include_file),
                                                                        bool(args.exclude_file),
                                                                        bool(args.include_type),
                                                                        bool(args.exclude_type))
        
        directory_filter: Callable[[str], bool] = lambda directory : True
        if (args.include_dir or args.exclude_dir):
            directory_set: frozenset[str] = frozenset(directory for directory in
                                                      (args.include_dir or args.exclude_dir))
            directory_filter = construct_directory_filter(directory_set,
                                                          include=bool(args.include_dir),
                                                          exclude=bool(args.exclude_dir))

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
            output_mapping["general"] = {"total" : line_data[0], "loc" : line_data[1]}
        else:
            language_record: dict[str, dict[str, int]] = {}
            kwargs.update({"language_record" : language_record})

            if args.verbosity == Verbosity.DETAILED:
                output_mapping.update(parse_directory_verbose(**kwargs))
                total, loc = output_mapping.pop("total"), output_mapping.pop("loc")
                output_mapping["general"] = {"total" : total, "loc" : loc}
            else:
                line_data: array[int] = array("L", (0, 0))
                parse_directory_record(**kwargs, line_data=line_data)
                output_mapping["general"] = {"total" : line_data[0], "loc" : line_data[1]}
            
            output_mapping["languages"] = language_record

    general_metadata: dict[str, str] = {"time" : f"{time.time()-epoch:.3f}s",
                                        "scanned_at" : datetime.now().strftime("%d/%m/%y, at %H:%M:%S"),
                                        "platform" : platform.system()}
    output_mapping["general"].update(general_metadata)  # type: ignore
        
    # Emit results
    output_file: Union[int, str] = sys.stdout.fileno()
    output_handler: OutputFunction = dump_std_output
    if args.output:
        assert isinstance(args.output, str)
        output_file = args.output.strip()
        output_extension: str = output_file.split(".")[-1]
        # Fetch output function based on file extension, default to standard write logic
        output_handler = OUTPUT_MAPPING.get(output_extension, output_handler)
    
    output_handler(output_mapping=output_mapping, filepath=output_file)
    return 0

def _run_guarded() -> NoReturn:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stdout.write(f"{__tool_name__} interrupted\n")
        sys.exit()


if __name__ == "__main__":
    _run_guarded()