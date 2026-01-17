'''Module to hold all parsing logic, at both file and directory levels'''
import os
from typing import Any, Callable, Iterator, Optional
from itertools import islice
import ctypes
from array import array

from cloc.ctypes_interfacing import lib, BatchScanResult
from cloc.data_structures.config import ClocConfig
from cloc.data_structures.typing import OutputMapping

def parse_file(filepath: str,
               singleline_symbol: Optional[bytes] = None,
               multiline_start_symbol: Optional[bytes] = None,
               multiline_end_symbol: Optional[bytes] = None,
               minimum_characters: int = 0) -> tuple[int, int]:
    loc: int = 0
    total: int = 0
    singleline_symbol_length: int = 0 if not singleline_symbol else len(singleline_symbol)
    multiline_start_symbol_length: int = 0 if not multiline_start_symbol else len(multiline_start_symbol)
    multiline_end_symbol_length: int = 0 if not multiline_end_symbol else len(multiline_end_symbol)

    with open(filepath, 'rb') as file:
        commentedBlock: bool = False            # Multiple multilineStarts will still have the same effect as one, so a single flag is enough

        while batch := list(islice(file, 100)):
            batchSize = len(batch)
            
            batchScanResult: BatchScanResult = lib.scanBatch((ctypes.c_char_p * batchSize)(*batch), batchSize, commentedBlock, minimum_characters, singleline_symbol, singleline_symbol_length, multiline_start_symbol, multiline_start_symbol_length, multiline_end_symbol, multiline_end_symbol_length)

            loc += batchScanResult.validLines
            total += batchSize

            commentedBlock = batchScanResult.commentedBlock
        return loc, total

def parse_directory(directory_data: Iterator[os.DirEntry[str]],
                    config: ClocConfig,
                    line_data: array[int],
                    file_filter_function: Callable = lambda _: True,
                    directory_filter_function: Callable = lambda _ : False,
                    minimum_characters: int = 0,
                    recurse: bool = False) -> None:
    for dir_entry in directory_data:
        if dir_entry.is_file():
            # File excluded
            if not file_filter_function(dir_entry.path):
                continue

            extension: str = dir_entry.name.split(".")[-1]
            if extension in config.ignored_languages:
                continue

            singleLine, multiLineStart, multiLineEnd = config.symbol_mapping.get(extension, (None, None, None))
            l, tl = parse_file(dir_entry.path,
                            singleLine, multiLineStart, multiLineEnd,
                            minimum_characters)
            line_data[0] += tl
            line_data[1] += l
            continue

        if not recurse:
            return
        
        parse_directory(os.scandir(dir_entry.path), config, line_data,
                        file_filter_function, directory_filter_function,
                        minimum_characters,
                        True)

def parse_directory_verbose(directory_data: Iterator[tuple[Any, list[Any], list[Any]]],
                            config: ClocConfig,
                            file_filter_function: Callable = lambda _: True,
                            directory_filter_function: Callable = lambda _ : False,
                            minimum_characters: int = 0,
                            recurse: bool = False,
                            loc: int = 0,
                            total_lines: int = 0,
                            outputMapping: Optional[dict] = None) -> OutputMapping:
    '''#### Iterate over every file in given root directory, and optionally perform the same for every file within its subdirectories\n
    #### args:
    directory_data: Output of os.walk() on root directory\n
    Function: Function to handle inclusion/exclusion logic at the file level (file names and file extensions)\n
    directory_filter_function: Function to handle inclusion/exclusion logic at the directory level
    level: Count of how many directories deep the current function is searching, increases per recursion

    #### returns:
    integer pair of loc and total lines scanned if no output path specified, else None
    '''
    ...
    # TODO: Remove complete materialisation of directory_data
    materialisedDirData: list = next(directory_data)
    rootDirectory: os.PathLike = materialisedDirData[0]

    if not outputMapping:
        outputMapping = {"general" : {}}
    for file in materialisedDirData[2]:
        # File excluded
        if not file_filter_function(file):
            continue

        extension: str = file.split(".")[-1]
        if extension in config.ignored_languages:
            continue

        singleLine, multiLineStart, multiLineEnd = config.symbol_mapping.get(extension, (None, None, None))

        l, tl = parse_file(os.path.join(rootDirectory, file), singleLine, multiLineStart, multiLineEnd, minimum_characters)
        total_lines += tl
        loc += l
        if not outputMapping.get(rootDirectory):
            outputMapping[rootDirectory] = {}
        outputMapping[rootDirectory][file] = {"loc" : l, "total_lines" : tl}
    outputMapping["general"]["loc"] = loc
    outputMapping["general"]["total"] = total_lines
    
    if not recurse:
        return outputMapping

    # All files have been parsed in this directory, recurse
    for dir in materialisedDirData[1]:
        if not directory_filter_function(dir):
            continue
        # Walk over and parse subdirectory
        subdirectoryData = os.walk(os.path.join(rootDirectory, dir))
        op = parse_directory_verbose(subdirectoryData, config, file_filter_function, directory_filter_function, minimum_characters, True)

        localLOC, localTotal = op.pop("general").values()
        outputMapping["general"]["loc"] = outputMapping["general"]["loc"] + localLOC
        outputMapping["general"]["total"] = outputMapping["general"]["total"] + localTotal
        outputMapping.update(op)


    return outputMapping