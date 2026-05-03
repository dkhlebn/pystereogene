"""Pytest configuration and fixtures for pystereogene tests."""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir() -> Path:
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def chrom_file(test_data_dir) -> Path:
    """Return the path to the test chromosome file."""
    return test_data_dir / "chromLength"


@pytest.fixture
def track_files(test_data_dir) -> list[Path]:
    """Return paths to test track files."""
    return [
        test_data_dir / "H3K4me1.bed",
        test_data_dir / "H3K4me3.bed",
    ]
