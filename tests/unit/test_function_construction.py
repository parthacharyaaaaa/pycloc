'''Unit tests for function construction logic'''

from typing import Callable
from locstat.utilities.core import (construct_directory_filter,
                                 construct_file_filter)

def test_directory_exclusion_filter():
    dummy_directories: list[str] = ["foo", "bar", "foo/bar", "foo/foo/bar"]
    excluded_directories: set[str] = {"bar", "foo/bar"}
    directory_filter: Callable[[str], bool] = construct_directory_filter(excluded_directories,
                                                                         exclude=True)
    for directory in dummy_directories:
        result: bool = directory_filter(directory)
        # Exclusion test
        if directory in excluded_directories:
            assert not result, \
            f"Directory '{directory}' incorrectly included by constructed filter"

        # !Excluded directories should pass
        else:
            assert result, \
            f"Directory '{directory}' incorrectly excluded by constructed filter"

def test_directory_inclusion_filter():
    dummy_directories: list[str] = ["foo", "bar", "foo/bar", "foo/foo/bar"]
    included_directories: set[str] = {"bar", "foo/bar"}
    directory_filter: Callable[[str], bool] = construct_directory_filter(included_directories,
                                                                         include=True)
    for directory in dummy_directories:
        result: bool = directory_filter(directory)
        # Inclusion test
        if directory in included_directories:
            assert result, \
            f"Directory '{directory}' incorrectly excluded by constructed filter"

        # !Included directories should not pass
        else:
            assert not result, \
            f"Directory '{directory}' incorrectly included by constructed filter"

def test_extension_inclusion_filter():
    dummy_files: list[str] = ["foo.py", "bar.pyi", "foo.c", "foo.h", "foo.cpp", "bar.java", ".py"]
    included_types: set[str] = {"py", "pyi", "c", "h"}
    file_filter: Callable[[str, str], bool] = construct_file_filter(included_types, include_type=True)

    for file in dummy_files:
        extension = file.rsplit(".", 1)[-1]
        result: bool = file_filter(file, extension)
        if extension in included_types:
            assert result, \
            f"Extension '{extension}' incorrectly excluded by constructed filter"

        else:
            assert not result, \
            f"Extension '{extension}' incorrectly included by constructed filter"

def test_extension_exclusion_filter():
    dummy_files: list[str] = ["foo.py", "bar.pyi", "foo.c", "foo.h", "foo.cpp", "bar.java", ".py"]
    excluded_types: set[str] = {"py", "pyi", "c", "h"}
    file_filter: Callable[[str, str], bool] = construct_file_filter(excluded_types, exclude_type=True)

    for file in dummy_files:
        extension = file.rsplit(".", 1)[-1]
        result: bool = file_filter(file, extension)
        if extension in excluded_types:
            assert not result, \
            f"Extension '{extension}' incorrectly included by constructed filter"

        else:
            assert result, \
            f"Extension '{extension}' incorrectly excluded by constructed filter"