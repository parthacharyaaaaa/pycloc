import csv
import json
import os
from types import MappingProxyType
from typing import Any, Final, Literal, Mapping, MutableMapping, Optional, Sequence, Union

from cloc.data_structures.typing import OutputFunction

__all__ = ("dump_std_output",
           "dump_json_output",
           "dump_csv_output",
           "OUTPUT_MAPPING")

def _format_row(row: Sequence[Union[str, int]], widths: Sequence[int]) -> str:
    return (
        f"{row[0]:<{widths[0]}}  "
        f"{row[1]:>{widths[1]}}  "
        f"{row[2]:>{widths[2]}}  "
        f"{row[3]:>{widths[3]}}\n"
    )

def dump_std_output(output_mapping: dict[str, Any],
                    filepath: Union[str, os.PathLike[str], int],
                    mode: Literal["w+", "a"] = "w+") -> None:
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
    with open(filepath, mode) as file:
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

def dump_json_output(output_mapping: dict[str, Any],
                     filepath: Union[str, os.PathLike[str], int],
                     mode: Literal["w+", "a"] = "w+") -> None:
    '''Dump output to JSON file, with proper formatting'''
    is_file_descriptor: bool = isinstance(filepath, int)
    if not (is_file_descriptor or os.path.abspath(filepath)):
        filepath = os.path.join(os.getcwd(), filepath)

    with open(filepath, mode=mode) as output_file:
        output_file.write(json.dumps(output_mapping, indent=2))

def dump_csv_output(output_mapping: dict[str, Any],
                    filepath: Union[str, os.PathLike[str], int],
                    mode: Literal["w+", "a"] = "w+") -> None:
    with open(filepath, newline='', mode=mode) as csvFile:
        writer = csv.writer(csvFile)
        assert isinstance(output_mapping["general"], MutableMapping)
        general_data: Optional[MutableMapping[str, Any]] = output_mapping.get("general")    #type: ignore

        if not general_data:
            writer.writerow(output_mapping.keys())
            writer.writerow(output_mapping.values())
        else:
            writer.writerow(general_data.keys())
            writer.writerow(general_data.values())
            writer.writerow(())

            # Write actual, per file data
            writer.writerow(("DIRECTORY", "FILE", "LOC", "TOTAL"))
            writer.writerow(())
            writer.writerows((dir, filename, fileData["loc"], fileData["total_lines"])
                             for dir, file in output_mapping.items()
                             for filename, fileData in file.items())    # type: ignore

OUTPUT_MAPPING: Final[MappingProxyType[str, OutputFunction]] = MappingProxyType({
    "json" : dump_json_output,
    "csv" : dump_csv_output,
})