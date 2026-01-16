import os
from typing import Any, Mapping, MutableMapping, Protocol, TypeAlias, Union

OutputMapping: TypeAlias = MutableMapping[str, Union[MutableMapping[str, Any], int, str]]

class OutputFunction(Protocol):
    def __call__(self,
                 output_mapping: Mapping[str, Mapping[str, Any]],
                 filepath: Union[str, os.PathLike[str]]) -> None:
        ...