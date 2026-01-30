import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from cloc.data_structures.exceptions import InvalidConfigurationException
from cloc.data_structures.singleton import SingletonMeta
from cloc.data_structures.typing import LanguageMetadata
from cloc.data_structures.verbosity import Verbosity

__all__ = ("ClocConfig",)

@dataclass(init=False, frozen=True, slots=True, weakref_slot=True)
class ClocConfig(metaclass=SingletonMeta):
    working_directory: Path

    # CLI Options
    verbosity: Verbosity = Verbosity.BARE
    minimum_characters: int = 0

    # Language metadata
    symbol_mapping: MappingProxyType[str, LanguageMetadata]
    ignored_languages: set[str]

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
                try:
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