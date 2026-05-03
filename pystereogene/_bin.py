"""Binary resolver for StereoGene executables."""

import os
import stat
from pathlib import Path

_BINARIES = ["StereoGene", "Smoother", "Binner", "Projector", "Confounder", "ParseGenes"]
_cache: dict[str, str] = {}


def _get_vendor_bin_dir() -> Path:
    """Get the path to the vendored bin directory."""
    return Path(__file__).parent / "_vendor" / "bin"


def _get_vendor_src_dir() -> Path:
    """Get the path to the vendored src directory."""
    return Path(__file__).parent / "_vendor" / "src"


def get_binary(name: str) -> str:
    """
    Get the absolute path to a StereoGene binary.

    Args:
        name: Binary name (StereoGene, Smoother, Binner, Projector, Confounder, ParseGenes)

    Returns:
        Absolute path to the executable.

    Raises:
        RuntimeError: If the binary is not found or not executable.
    """
    if name in _cache:
        return _cache[name]

    if name not in _BINARIES:
        raise ValueError(f"Unknown binary: {name}. Must be one of {_BINARIES}")

    bin_dir = _get_vendor_bin_dir()
    path = bin_dir / name

    if not path.is_file():
        raise RuntimeError(
            f"StereoGene binary '{name}' not found at {path}. "
            "Run: python -m pystereogene.build"
        )

    if not os.access(path, os.X_OK):
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    _cache[name] = str(path)
    return _cache[name]


def binaries_available() -> bool:
    """Check if all binaries are available."""
    bin_dir = _get_vendor_bin_dir()
    return all((bin_dir / name).is_file() for name in _BINARIES)
