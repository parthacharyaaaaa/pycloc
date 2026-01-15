'''Helper functions'''
from types import MappingProxyType
import csv
import os
from typing import Mapping, Optional, Union

from cloc.config import LANGUAGES

# Dynamic import in case orjson is found in the Python environment (vroom vroom)
bOrjson: bool = True
try:
    import orjson
except ImportError:
    bOrjson = False
    import json

def getVersion():
    with open(os.path.join(os.path.dirname(__file__), "config.json")) as config:
        if bOrjson:
            version: str = orjson.loads(config.read()).get("version")
        else:
            version: str = json.loads(config.read()).get("version")
        if not version:
            print("py-cloc: version not found!")
        else:
            print(f"py-cloc {version}")

def findCommentSymbols(extension: str,
                       symbolMapping: Union[Mapping[str, Mapping[str, str]], None] = None
                       ) -> Union[bytes, tuple[bytes, bytes], tuple[bytes, tuple[bytes, bytes]]]:
        '''### Find symbols that denote a comment for a specific language
        
        #### args
        extension: File extension of the language\n
        symbolMapping: Mapping of file extensions and their corresponding symbols. Keys are `symbols` for single-line comments and `multilined` for multi-line comments. See `languages.json` for the actual mapping'''

        extension = extension.strip().lower()
        if not symbolMapping:
            symbolMapping = LANGUAGES

        singleline_symbol: Optional[str] = symbolMapping["symbols"].get(extension)
        multiline_symbols: Optional[str] = symbolMapping["multilined"].get(extension)
        multiline_symbol_pair: Optional[list[str]] = None

        if not (singleline_symbol or multiline_symbols):
            raise ValueError(f"No comment symbols found for extension .{extension}")
        
        if multiline_symbols:
            multiline_symbol_pair = multiline_symbols.split()
            if not len(multiline_symbol_pair) == 2:
                raise ValueError(f"Invalid syntax for multiline comments for extension: .{extension}")
        
        if not singleline_symbol:
            assert multiline_symbol_pair
            return multiline_symbol_pair[0].encode(), multiline_symbol_pair[1].encode()
        if not multiline_symbol_pair:
            return singleline_symbol.encode()
        
        return (singleline_symbol.encode(),
                (multiline_symbol_pair[0].encode(), multiline_symbol_pair[1].encode()))

def dumpOutputSTD(outputMapping: dict, fpath: os.PathLike) -> None:
    '''Dump output to a standard text/log file'''
    with open(fpath, "w+") as file:
        if not outputMapping.get("general"):
            file.write("\n".join(f"{k} : {v}" for k,v in outputMapping.items()))
            return
        
        mainMetadata: str = "\n".join(f"{k} : {v}" for k,v in outputMapping.pop("general").items())
        file.write(mainMetadata)
        file.write("\n"+"="*15+"\n")
        outputString: str = ""
        for directory, entries in outputMapping.items():
            outputString = "\n".join(f"\t{k}:LOC: {v['loc']} Total: {v['total_lines']}" for k,v in entries.items())
            file.write(f"{directory}\n{outputString}\n")

def dumpOutputJSON(outputMapping: dict, fpath: os.PathLike) -> None:
    '''Dump output to JSON file, with proper formatting'''
    if bOrjson:
        with open(os.path.join(os.getcwd(), fpath), "wb+") as dumpFile:
            dumpFile.write(orjson.dumps(outputMapping, option=orjson.OPT_INDENT_2, default=dict))
        return

    with open(os.path.join(os.getcwd(), fpath), "w+") as dumpFile:
        dumpFile.write(json.dumps(outputMapping, skipkeys=True,
                                ensure_ascii=True,
                                indent="\t",
                                default=dict))

def dumpOutputSQL(outputMapping: dict, fpath: os.PathLike) -> None:
    '''Dump output to a SQLite database (.db, .sql)'''
    # Best language fr, has SQL API built-in
    import sqlite3
    
    dbConnection: sqlite3.Connection = sqlite3.connect(fpath, isolation_level="IMMEDIATE")
    dbCursor: sqlite3.Cursor = dbConnection.cursor()

    # No context manager protocol in sqlite3 cursors :(
    try:
        # Enable Foreign Keys if this current driver hasn't done so already
        dbCursor.execute("PRAGMA foreign_keys = ON;")

        # DDL
        dbCursor.execute('''
                         CREATE TABLE IF NOT EXISTS general (LOC INTEGER DEFAULT 0,
                         total_lines INTEGER DEFAULT 0,
                         time DATETIME,
                         platform VARCHAR(32));
                         ''')
        
        # DML
        if not outputMapping.get("general"):
            # !Verbose, insert general data and exit
            dbConnection.execute("DELETE FROM general;")            
            dbConnection.execute("INSERT INTO general VALUES (?, ?, ?, ?)", (outputMapping["loc"], outputMapping["total"], outputMapping["time"], outputMapping["platform"]))
            dbConnection.commit()
        
        else:
            dbCursor.execute('''
                            CREATE TABLE IF NOT EXISTS file_data (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            directory VARCHAR(1024) NOT NULL,
                            _name VARCHAR(1024) NOT NULL,
                            LOC INTEGER DEFAULT 0,
                            total_lines INTEGER DEFAULT 0);
                            ''')
            dbConnection.commit()
            # Clear out all previous data
            for table in ("general","file_data"):
                dbConnection.execute(f"DELETE FROM {table}")
            dbConnection.commit()

            dbConnection.execute("INSERT INTO general VALUES (?, ?, ?, ?)", (outputMapping['general']["loc"], outputMapping['general']["total"], outputMapping['general']["time"], outputMapping['general']["platform"]))
            
            outputMapping.pop("general")
            for directory, fileMapping in outputMapping.items():
                dbCursor.executemany("INSERT INTO file_data (directory, _name, LOC, total_lines) VALUES (?, ?, ?, ?);",
                                    ([directory, filename, fileData["loc"], fileData["total_lines"]] for filename, fileData in fileMapping.items()))
            dbConnection.commit()
    finally:
        if dbCursor:
            dbCursor = None
        dbConnection.close()
        dbConnection = None

def dumpOutputCSV(outputMapping: dict, fpath: os.PathLike) -> None:
    with open(fpath, newline='', mode="w+") as csvFile:
        writer = csv.writer(csvFile)
        generalData: dict = outputMapping.get("general")

        if not generalData:
            writer.writerow(outputMapping.keys())
            writer.writerow(outputMapping.values())
        else:
            generalData.pop("general")
            writer.writerow(generalData.keys())
            writer.writerow(generalData.values())
            writer.writerow(())

            # Write actual, per file data
            writer.writerow(("DIRECTORY", "FILE", "LOC", "TOTAL"))
            writer.writerow(())
            writer.writerows((dir, filename, fileData["loc"], fileData["total_lines"]) for dir, file in outputMapping.items() for filename, fileData in file.items())

OUTPUT_MAPPING: MappingProxyType = MappingProxyType({
    "json" : dumpOutputJSON,
    "db" : dumpOutputSQL,
    "sql" : dumpOutputSQL,
    "csv" : dumpOutputCSV,
    "txt" : dumpOutputSTD,
    "log" : dumpOutputSTD,
    None : dumpOutputSTD
})