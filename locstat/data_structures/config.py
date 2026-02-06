from enum import StrEnum
import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from locstat.data_structures.exceptions import InvalidConfigurationException
from locstat.data_structures.singleton import SingletonMeta
from locstat.data_structures.typing import LanguageMetadata
from locstat.data_structures.verbosity import Verbosity
from locstat.data_structures.parse_modes import ParseMode

__all__ = ("ClocConfig",)

@dataclass(init=False, slots=True, weakref_slot=True)
class ClocConfig(metaclass=SingletonMeta):
    working_directory: Path

    # CLI Options
    verbosity: Verbosity = Verbosity.BARE
    minimum_characters: int = 0
    max_depth: int = -1
    parsing_mode: ParseMode = ParseMode.BUFFERED

    # Language metadata
    symbol_mapping: MappingProxyType[str, LanguageMetadata]
    ignored_languages: set[str]

    config_file: str

    additional_kwargs: dict[str, Any] = field(default_factory = dict)

    @property
    def configurable(self) -> frozenset[str]:
        return frozenset(["verbosity", "minimum_characters",
                          "max_depth", "parsing_mode"])

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
        object.__setattr__(instance, "config_file", config_file)

        additional_kwargs: dict[str, Any] = {}
        for tag, attr in config_dict.items():
            if tag not in instance.__slots__:
                additional_kwargs[tag] = attr
                continue
            if not isinstance(attr, cls.__annotations__[tag]):
                try:
                    if issubclass(cls.__annotations__[tag], (ParseMode, Verbosity)):
                        attr = attr.upper()
                    attr = cls.__annotations__[tag](attr)
                except (ValueError, TypeError):
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
            languages_data = json.loads(langauges_source.read())

        object.__setattr__(instance, "ignored_languages", set(languages_data.pop("ignore")))
        
        comments_data: dict[str, list[str]] = languages_data.pop("comments")
        symbol_mapping: dict[str, LanguageMetadata] = {}
        for language, comment_data in comments_data.items():
            if len(comment_data) != 3:
                raise InvalidConfigurationException(" ".join((f"Comment data for file extension {language} malformed",
                                                              "Should be of format:",
                                                              "(singleline, multiline-start, multiline-end)",
                                                              f"got {comment_data} instead")))
            singleline, multistart, multiend = comment_data
            symbol_mapping[language] = (singleline.encode() if singleline else None,
                                        multistart.encode() if multistart else None,
                                        multiend.encode() if multiend else None)
        object.__setattr__(instance, "symbol_mapping", symbol_mapping)
        return instance
    
    @property
    def configurations(self) -> dict[str, Any]:
        return {config_key : getattr(self, config_key)
                for config_key in sorted(self.configurable)}
    
    @property
    def configurations_string(self) -> str:
        return "\n".join(f"{k} : {v}" for k,v in self.configurations.items())
    
    @staticmethod
    def _cast_toml_dtype(value: str|int) -> str|int:
        if isinstance(value, bool):
            return str(value).lower()
        return value

    @staticmethod
    def config_default_toml_dumps(d: dict[str, Any]) -> str:
        lines: list[str] = ["[defaults]"]
        for k, v in d.items():
            casted: str|int = ClocConfig._cast_toml_dtype(v)
            if isinstance(casted, str):
                casted = f"\"{casted}\""
            lines.append("=".join((k, str(casted))))
        return "\n".join(lines)

    def update_configuration(self, configuration: str, value: Any) -> None:
        if configuration not in self.configurable:
            raise ValueError(f"Item {configuration} not supported")
        
        datatype: type[Any] = ClocConfig.__annotations__[configuration]
        if not isinstance(value, datatype):
            try:
                # What an awful hack
                if issubclass(datatype, (ParseMode, Verbosity)):
                    value = value.upper()
                value = datatype(value)
            except (ValueError, TypeError):
                raise InvalidConfigurationException(" ".join((f"Value {value} unsupported",
                                                              f"for configuration {configuration},"
                                                              "expected type:",
                                                              str(datatype).split("'")[1])))
        setattr(self, configuration, value)
        with open(self.config_file, "w") as config_file:
            config_file.write(ClocConfig.config_default_toml_dumps(self.configurations))