from pathlib import Path
from typing import Iterable

from cloc.parsing.extensions._parsing import (_parse_file_vm_map,
                                              _parse_file_no_chunk,
                                              _parse_file)
from cloc.data_structures.typing import FileParsingFunction, LanguageMetadata
from tests.fixtures import mock_dir

def _test_helper_run_all_parsers(file: Path,
                                 comment_data: LanguageMetadata,
                                 expected_total: int, expected_loc: int,
                                 minimum_characters: int = 0,
                                 parsers: Iterable[FileParsingFunction] = (_parse_file, _parse_file_no_chunk, _parse_file_vm_map)):
    results: dict[FileParsingFunction, tuple[int, int]] = {parser : parser(str(file), *comment_data, minimum_characters)
                                                           for parser in parsers}
    failures: list[str] = [", ".join((parser.__qualname__,
                                      f"Total: Expected = {expected_total}, Observed = {total}",
                                      f"LOC: Expected = {expected_loc}, Observed = {loc}"))
                           for parser, (total, loc) in results.items()
                           if (total, loc) != (expected_total, expected_loc)]
    assert not failures, \
    "\n".join(failures)

def test_parsing_singleline_only(mock_dir) -> None:
    lines: list[str] = ["# This is a comment",
                        "def foo(arg: int) -> None:",
                        "\tos.remove('/')",
                        "\t# Here's another comment",
                        "",
                        "\treturn None"]

    expected_total, expected_loc = len(lines), 3
    mock_file: Path = mock_dir / "_mock_file.py"
    mock_file.touch()
    mock_file.write_text("\n".join(lines))
    
    _test_helper_run_all_parsers(mock_file, (b"#", None, None), expected_total, expected_loc)

def test_parsing_multiline_only(mock_dir) -> None:
    lines: list[str] = ["/* This is a comment",
                        "This is a continuation",
                        "This is a continuation",
                        "This is a continuation",
                        "All good things must come to an end */",
                        "",
                        "#include <stdlib.h>",
                        "int main(){",
                        "\tint x = 10;",
                        "\tbool y = false;",
                        "/* Look whos here again!",
                        "This is a continuation",
                        "Bye bye! */",
                        "return 0;",
                        "}"]

    expected_total, expected_loc = len(lines), 6
    mock_file: Path = mock_dir / "_mock_file.c"
    mock_file.touch()
    mock_file.write_text("\n".join(lines))

    _test_helper_run_all_parsers(mock_file, (b"//", b"/*", b"*/"), expected_total, expected_loc)

def test_parsing_nested(mock_dir) -> None:
    lines: list[str] = ['// Nested comments!',
                        "/* Here's a multiline block",
                        '//',
                        '// */',
                        '// The above line should end the commmented block',
                        'int main(){return 0;}']

    expected_total, expected_loc = len(lines), 1
    mock_file: Path = mock_dir / "_mock_file.c"
    mock_file.touch()
    mock_file.write_text("\n".join(lines))

    _test_helper_run_all_parsers(mock_file, (b"//", b"/*", b"*/"), expected_total, expected_loc)
    
def test_parsing_inline(mock_dir) -> None:
    lines: list[str] = ['int main(){',
                        "return /* Here's Johnny! */ 0;",
                        "}"]

    expected_total, expected_loc = len(lines), 3
    mock_file: Path = mock_dir / "_mock_file.c"
    mock_file.touch()
    mock_file.write_text("\n".join(lines))

    _test_helper_run_all_parsers(mock_file, (b"//", b"/*", b"*/"), expected_total, expected_loc)

def test_asymmetric_multiline_symbols(mock_dir) -> None:
    lines: list[str] = ["<!-- Start",
                        "Continuation",
                        "End -->"]

    expected_total, expected_loc = len(lines), 0

    mock_file: Path = mock_dir / "_mock_file.html"
    mock_file.touch()
    mock_file.write_text("\n".join(lines))

    _test_helper_run_all_parsers(mock_file, (None, b"<!--", b"-->"), expected_total, expected_loc)
        