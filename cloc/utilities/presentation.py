import csv
import json
import os
from types import MappingProxyType
from typing import Any, Final, Literal, Mapping, MutableMapping, Optional, Union

from cloc.data_structures.typing import OutputFunction, OutputMapping

__all__ = ("dump_std_output",
           "dump_json_output",
           "dump_csv_output",
           "OUTPUT_MAPPING")

def dump_std_output(output_mapping: OutputMapping,
                    filepath: Union[str, os.PathLike[str], int],
                    mode: Literal["w+", "a"] = "w+") -> None:
    '''Dump output to a standard text/log file'''
    with open(filepath, mode) as file:
        if not output_mapping.get("general"):
            file.write("\n".join(f"{k} : {v}" for k,v in output_mapping.items()))
            return
        
        assert isinstance(output_mapping["general"], MutableMapping)
        metadata: str = "\n".join(f"{k} : {v}" for k,v in output_mapping["general"].items())
        file.write(metadata)
        file.write("\n"+"="*15+"\n")
        output_string: str = ""
        output_mapping.pop("general")
        
        for directory, entries in output_mapping.items():
            assert isinstance(entries, Mapping)
            output_string = "\n".join(f"\t{k}:LOC: {v['loc']} Total: {v['total_lines']}" for k,v in entries.items())
            file.write(f"{directory}\n{output_string}\n")

def dump_json_output(output_mapping: OutputMapping,
                     filepath: Union[str, os.PathLike[str], int],
                     mode: Literal["w+", "a"] = "w+") -> None:
    '''Dump output to JSON file, with proper formatting'''
    is_file_descriptor: bool = isinstance(filepath, int)
    if not (is_file_descriptor or os.path.abspath(filepath)):
        filepath = os.path.join(os.getcwd(), filepath)

    with open(filepath, mode=mode) as output_file:
        output_file.write(json.dumps(output_mapping, indent=2))

def dump_csv_output(output_mapping: OutputMapping,
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
    "txt" : dump_std_output,
    "log" : dump_std_output
})