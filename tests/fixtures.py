from dataclasses import dataclass, field

import pytest

from cloc.data_structures.verbosity import Verbosity

@dataclass
class MockConfig:
    verbosity: Verbosity = field(default=Verbosity.BARE)
    minimum_characters: int = field(default=1)

@pytest.fixture
def mock_config() -> MockConfig:
    return MockConfig()

@pytest.fixture
def mock_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("_temp_dir")
    return path