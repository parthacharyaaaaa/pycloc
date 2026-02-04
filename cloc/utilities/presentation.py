import json
import os
from io import TextIOWrapper
from types import MappingProxyType
from typing import (Any, Final, Literal,
                    Optional, Sequence,
                    Union)

from cloc.data_structures.typing import OutputFunction

__all__ = ("dump_std_output",
           "dump_json_output",
           "OUTPUT_MAPPING")

def _format_row(row: Sequence[Union[str, int]], widths: Sequence[int]) -> str:
    return (
        f"{row[0]:<{widths[0]}}  "
        f"{row[1]:>{widths[1]}}  "
        f"{row[2]:>{widths[2]}}  "
        f"{row[3]:>{widths[3]}}\n"
    )

def _dump_directory_tree(
    file: TextIOWrapper,
    name: str,
    node: dict[str, Any],
    prefix: str = "",
    is_last: bool = True,
) -> None:
    connector: str = "└── " if is_last else "├── "
    next_prefix: str = prefix + ("    " if is_last else "│   ")
    total, loc = node.get("total"), node.get("loc")
    header = f"{name}/ (total={total or 'N/A'}, loc={loc or 'N/A'})"

    file.write(f"{prefix}{connector}{header}\n")

    files: dict[str, Any] = node.get("files", {})
    file_items: list[tuple[str, dict[str, int]]] = sorted(files.items())

    for idx, (path, meta) in enumerate(file_items):
        is_last_file: bool = idx == len(file_items) - 1 and not node.get("subdirectories")
        file_connector: str = "└── " if is_last_file else "├── "
        fname = os.path.basename(path)

        file.write(
            f"{next_prefix}{file_connector}"
            f"{fname} (total={meta.get('total_lines')}, loc={meta.get('loc')})\n"
        )

    # Subdirectories (recursive)
    subdirs = node.get("subdirectories", {})
    sub_items = sorted(subdirs.items())

    for idx, (subname, subnode) in enumerate(sub_items):
        _dump_directory_tree(
            file,
            subname,
            subnode,
            prefix=next_prefix,
            is_last=idx == len(sub_items) - 1,
        )

def dump_std_output(output_mapping: dict[str, Any],
                    filepath: Union[str, os.PathLike[str], int]) -> None:
    '''
    Dump output to a standard text/log file
    
    :param output_mapping: resultant mapping
    :type output_mapping: dict[str, Any]
    
    :param filepath: Output file to write results to, can be stdout
    :type filepath: Union[str, os.PathLike[str], int]

    :param mode: Writing mode
    :type mode: Literal["w+", "a"]
    '''
    assert isinstance(output_mapping["general"], dict)
    with open(filepath, "w") as file:
        file.write("GENERAL:\n")
        file.write("\n".join(f"{field} : {value}" for field, value in output_mapping["general"].items()))
        
        file.write("\n\n")

        languages: Optional[dict[str, dict[str, int]]] = output_mapping.pop("languages", None)
        if languages:
            headers: list[str] = ["Extension", "Files", "Total", "LOC"]

            rows = [
                (lang, data["files"], data["total"], data["loc"])
                for lang, data in languages.items()
            ]

            widths = [
                max(len(str(col)) for col in column)
                for column in zip(headers, *rows)
            ]

            file.write("LANGUAGE METADATA\n")
            file.write(_format_row(headers, widths))
            file.write("-" * (sum(widths) + 6))
            file.write("\n")

            for row in rows:
                file.write(_format_row(row, widths))

        tree = output_mapping.get("subdirectories")
        if tree:
            file.write("\nFILES & DIRECTORIES\n")
            for idx, (name, node) in enumerate(sorted(tree.items())):
                _dump_directory_tree(
                    file,
                    name,
                    node,
                    prefix="",
                    is_last=idx == len(tree) - 1,
                )

def dump_json_output(output_mapping: dict[str, Any],
                     filepath: Union[str, os.PathLike[str], int]) -> None:
    '''Dump output to JSON file, with proper formatting'''
    is_file_descriptor: bool = isinstance(filepath, int)
    if not (is_file_descriptor or os.path.abspath(filepath)):
        filepath = os.path.join(os.getcwd(), filepath)

    with open(filepath, mode="w") as output_file:
        output_file.write(json.dumps(output_mapping, indent=2))

OUTPUT_MAPPING: Final[MappingProxyType[str, OutputFunction]] = MappingProxyType({
    "json" : dump_json_output,
})