import os
from array import array
from typing import Any, Callable, Iterator, Optional

from cloc.data_structures.config import ClocConfig
from cloc.data_structures.typing import FileParsingFunction

__all__ = ("parse_directory",
           "parse_directory_verbose")

def parse_directory(
        directory_data: Iterator[os.DirEntry[str]],
        config: ClocConfig,
        line_data: array[int],
        file_parsing_function: FileParsingFunction,
        file_filter_function: Callable = lambda _: True,
        directory_filter_function: Callable = lambda _ : False,
        minimum_characters: int = 0,
        recurse: bool = False) -> None:
    '''
    Parse directory and calculate LOC and total lines
    
    :param directory_data: Iterator over top directory
    :type directory_data: Iterator[os.DirEntry[str]]

    :param config: Caller's configuration instance
    :type config: ClocConfig

    :param line_data: 2-element integer sequence to store total lines and LOC
    :type line_data: array.array

    :param file_parsing_function: Parsing function called for each file
    :type config: FileParsingFunction

    :param file_filter_function: Filter function to include/exclude files
    :type file_filter_function: Callable

    :param directory_filter_function: Filter function to exclude/include directories
    :type directory_filter_function: Callable

    :param minimum_characters: Minimum characters per line for it to be counted as a line of code
    :type minimum_characters: int
    
    :param recurse: Flag to scan subdirectories
    :type recurse: bool

    :return: Passed line_data array is updated
    :rtype: NoneType
    '''
    for dir_entry in directory_data:
        if dir_entry.is_file():
            # File excluded
            if not file_filter_function(dir_entry.path):
                continue

            extension: str = dir_entry.name.split(".")[-1]
            if extension in config.ignored_languages:
                continue

            singleLine, multiLineStart, multiLineEnd = config.symbol_mapping.get(extension, (None, None, None))
            tl, l = file_parsing_function(dir_entry.path,
                                          singleLine, multiLineStart, multiLineEnd,
                                          minimum_characters)
            line_data[0] += tl
            line_data[1] += l
            continue

        if not recurse:
            return
        
        parse_directory(os.scandir(dir_entry.path), config, line_data,
                        file_parsing_function, file_filter_function, directory_filter_function,
                        minimum_characters,
                        True)

def parse_directory_verbose(
    directory_data: Iterator[os.DirEntry[str]],
    config: ClocConfig,
    file_parsing_function: FileParsingFunction,
    file_filter_function: Callable = lambda _: True,
    directory_filter_function: Callable = lambda _: False,
    minimum_characters: int = 0,
    recurse: bool = False,
    *,
    output_mapping: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    '''
    Parse directory and include children file and subdirectory data
    
    :param directory_data: Iterator over top directory
    :type directory_data: Iterator[os.DirEntry[str]]
    :param config: Caller's configuration instance
    :type config: ClocConfig
    :param file_parsing_function: Parsing function called for each file
    :type config: FileParsingFunction
    :param file_filter_function: Filter function to include/exclude files
    :type file_filter_function: Callable
    :param directory_filter_function: Filter function to exclude/include directories
    :type directory_filter_function: Callable
    :param minimum_characters: Minimum characters per line for it to be counted as a line of code
    :type minimum_characters: int
    :param recurse: Flag to scan subdirectories
    :type recurse: bool
    :param output_mapping: Mapping returned in recursive calls for aggregation.
    There is no need to pass arguments for this paraneter
    :type output_mapping: Optional[dict[str, Any]]
    :return: Mapping of LOC and line information
    :rtype: dict[str, Any]
    '''

    if output_mapping is None:
        output_mapping = {}

    directory_total = directory_loc = 0
    files: dict[str, Any] = {}
    subdirectories: dict[str, Any] = {}

    for dir_entry in directory_data:
        if dir_entry.is_file():
            if not file_filter_function(dir_entry.path):
                continue

            extension = dir_entry.name.rsplit(".", 1)[-1]
            if extension in config.ignored_languages:
                continue

            single, multi_start, multi_end = config.symbol_mapping.get(
                extension, (None, None, None)
            )

            file_loc, file_total = file_parsing_function(
                dir_entry.path,
                single,
                multi_start,
                multi_end,
                minimum_characters,
            )

            directory_total += file_total
            directory_loc += file_loc

            files[dir_entry.path] = {
                "loc": file_loc,
                "total_lines": file_total,
            }

        elif (recurse
              and dir_entry.is_dir()
              and directory_filter_function(dir_entry.path)):
            with os.scandir(dir_entry.path) as directory_iterator:
                child = parse_directory_verbose(
                    directory_iterator,
                    config,
                    file_parsing_function,
                    file_filter_function,
                    directory_filter_function,
                    minimum_characters,
                    True)

            subdirectories[dir_entry.name] = child
            directory_total += child["total"]
            directory_loc += child["loc"]

    output_mapping.update({
        "files": files,
        "subdirectories": subdirectories,
        "total": directory_total,
        "loc": directory_loc,
    })

    return output_mapping
