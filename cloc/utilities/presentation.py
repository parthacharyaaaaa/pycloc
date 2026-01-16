import csv
import os
import platform
import sqlite3
from types import MappingProxyType
from typing import Any, Final, Literal, Mapping, MutableMapping, Optional, Union

import orjson

from cloc.data_structures.typing import OutputFunction, OutputMapping

__all__ = ("dump_std_output",
           "dump_json_output",
           "dump_sql_output",
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

    with open(filepath, mode=mode+"b") as output_file:
        output_file.write(orjson.dumps(output_mapping,
                                       option=orjson.OPT_INDENT_2,
                                       default=dict))

def dump_sql_output(output_mapping: OutputMapping,
                    filepath: Union[str, os.PathLike[str], int],
                    mode: Literal["w+", "a"] = "w+") -> None:
    '''Dump output to a SQLite database (.db, .sql)''' 
    if isinstance(filepath, int):
        if platform.system().lower() == "windows":
            raise ValueError("Cannot open SQLite3 db file on Windows using file descriptor")
        filepath = os.readlink("/".join(("proc", "self", "fd", str(filepath))))
    
    db_conn: sqlite3.Connection = sqlite3.connect(filepath, isolation_level="IMMEDIATE")
    db_cursor: sqlite3.Cursor = db_conn.cursor()

    # No context manager protocol in sqlite3 cursors :(
    try:
        # Enable Foreign Keys if this current driver hasn't done so already
        db_cursor.execute("PRAGMA foreign_keys = ON;")

        # DDL
        db_cursor.execute('''
                         CREATE TABLE IF NOT EXISTS general (
                         LOC INTEGER DEFAULT 0,
                         total_lines INTEGER DEFAULT 0,
                         time DATETIME,
                         platform VARCHAR(32)
                         );''')
        
        # DML
        if not output_mapping.get("general"):
            # !Verbose, insert general data and exit
            db_conn.execute("DELETE FROM general;")            
            db_conn.execute("INSERT INTO general VALUES (?, ?, ?, ?)",
                                 (output_mapping["loc"], output_mapping["total"],
                                  output_mapping["time"], output_mapping["platform"]))
            db_conn.commit()
        
        else:
            db_cursor.execute('''
                            CREATE TABLE IF NOT EXISTS file_data (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            directory VARCHAR(1024) NOT NULL,
                            _name VARCHAR(1024) NOT NULL,
                            LOC INTEGER DEFAULT 0,
                            total_lines INTEGER DEFAULT 0);
                            ''')
            db_conn.commit()
            # Clear out all previous data
            for table in ("general","file_data"):
                db_conn.execute(f"DELETE FROM {table}")
            db_conn.commit()

            assert isinstance(output_mapping["general"], Mapping)
            db_conn.execute("INSERT INTO general VALUES (?, ?, ?, ?)",
                            (output_mapping['general']["loc"], output_mapping['general']["total"],
                             output_mapping['general']["time"], output_mapping['general']["platform"]))
            
            for directory, fileMapping in output_mapping.items():
                assert isinstance(fileMapping, Mapping)
                db_cursor.executemany('''INSERT INTO file_data (directory, _name, LOC, total_lines)
                                      VALUES (?, ?, ?, ?);''',
                                    ([directory, filename, fileData["loc"], fileData["total_lines"]]
                                     for filename, fileData in fileMapping.items()))
            db_conn.commit()
    finally:
        db_cursor.close()
        db_conn.close()

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
    "db" : dump_sql_output,
    "sql" : dump_sql_output,
    "csv" : dump_csv_output,
    "txt" : dump_std_output,
    "log" : dump_std_output
})