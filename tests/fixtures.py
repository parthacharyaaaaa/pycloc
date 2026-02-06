from dataclasses import dataclass, field

import pytest

from locstat.data_structures.verbosity import Verbosity
from locstat.data_structures.parse_modes import ParseMode

@dataclass
class MockConfig:
    verbosity: Verbosity = field(default=Verbosity.BARE)
    minimum_characters: int = field(default=1)
    max_depth: int = field(default=-1)
    parsing_mode: ParseMode = field(default=ParseMode.BUFFERED)

    @property
    def configurable(self) -> frozenset[str]:
        return frozenset(["verbosity", "minimum_characters",
                          "max_depth", "parsing_mode"])

@pytest.fixture
def mock_config() -> MockConfig:
    return MockConfig()

@pytest.fixture
def mock_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("_temp_dir")
    return path