from dataclasses import dataclass, field

import pytest

@dataclass
class MockConfig:
    recurse: bool = field(default=False)
    verbose: bool = field(default=False)
    minimum_characters: int = field(default=0)

@pytest.fixture
def mock_config() -> MockConfig:
    return MockConfig(
        recurse=False,
        verbose=False,
        minimum_characters=0
    )

@pytest.fixture
def mock_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("_temp_dir")
    return path