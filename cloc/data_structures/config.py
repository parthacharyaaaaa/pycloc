import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional, Union

from .singleton import SingletonMeta
from .exceptions import InvalidConfigurationException

import orjson

__all__ = ("ClocConfig",)

@dataclass(init=False, frozen=True, slots=True, weakref_slot=True)
class ClocConfig(metaclass=SingletonMeta):
    # Some shit idk man
    working_directory: Path

    # CLI Options
    recurse: bool = False
    verbose: bool = True
    minimum_characters: int = 0

    # Language metadata
    language_metadata: MappingProxyType[str, MappingProxyType[str, str]]
    ignored_languages: frozenset[str]

    additional_kwargs: dict[str, Any] = field(default_factory = dict)

    @staticmethod
    def flatten_mapping(mapping: Mapping[Any, Any]) -> dict[Any, Any]:
        flattened: dict[Any, Any] = {}
        leftover: list[Mapping[Any, Any]] = [mapping]
        while leftover:
            popped_map: Mapping[Any, Any] = leftover.pop(0)
            for k, v in popped_map.items():
                if isinstance(v, Mapping):
                    leftover.append(popped_map[k])
                    continue
                flattened[k] = v
        return flattened

    @classmethod
    def load_toml(cls, config_file: Path) -> 'ClocConfig':
        with open(config_file, 'r', encoding="utf-8") as configurations:
            config_dict: dict[str, Any] = cls.flatten_mapping(tomllib.loads(configurations.read()))
        instance: ClocConfig = cls()

        additional_kwargs: dict[str, Any] = {}
        for tag, attr in config_dict.items():
            if tag not in instance.__slots__:
                additional_kwargs[tag] = attr
                continue
            if not isinstance(attr, cls.__annotations__[tag]):
                raise InvalidConfigurationException(
                    message=" ".join((f"Invalid type {type(attr)} for configuration attribute {tag},",
                                      f"expected {cls.__annotations__[tag]}"))
                )
            object.__setattr__(instance, tag, attr)

        object.__setattr__(instance, "additional_kwargs", additional_kwargs)

        working_directory: Path = Path(__file__).parent.parent
        object.__setattr__(instance, "working_directory", working_directory)

        # Load data about comment symbols
        with open(working_directory / "languages.json", "rb") as langauges_source:
            languages_data = orjson.loads(langauges_source.read())
        
        languages: MappingProxyType[str, MappingProxyType[str, str]] = MappingProxyType(
            {"symbols" : languages_data.pop("symbols"),
                "multilined" : languages_data.pop("multilined")}
        )
        object.__setattr__(instance, "language_metadata", languages)
        object.__setattr__(instance, "ignored_languages", frozenset(languages_data.pop("ignore")))
        return instance
    
    def find_comment_symbol(self,
                            extension: str
                            ) -> Union[bytes, tuple[bytes, bytes], tuple[bytes, tuple[bytes, bytes]]]:
        extension = extension.strip(". ").lower()
        
        singleline_symbol: Optional[str] = self.language_metadata["symbols"].get(extension)
        multiline_symbols: Optional[str] = self.language_metadata["multilined"].get(extension)
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