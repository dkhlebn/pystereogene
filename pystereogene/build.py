"""Build StereoGene binaries from source."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

BINARIES = ["StereoGene", "Smoother", "Binner", "Projector", "Confounder", "ParseGenes"]


def get_src_dir() -> Path:
    """Get the path to the C++ source directory."""
    return Path(__file__).parent / "_vendor" / "src"


def get_bin_dir() -> Path:
    """Get the path to store compiled binaries."""
    return Path(__file__).parent / "_vendor" / "bin"


def build(src_dir: Path | None = None, bin_dir: Path | None = None, jobs: int | None = None) -> None:
    """
    Build StereoGene binaries from source.

    Args:
        src_dir: Path to C++ source directory. Defaults to _vendor/src.
        bin_dir: Path to store binaries. Defaults to _vendor/bin.
        jobs: Number of parallel make jobs. Defaults to CPU count.
    """
    if src_dir is None:
        src_dir = get_src_dir()
    if bin_dir is None:
        bin_dir = get_bin_dir()
    if jobs is None:
        jobs = os.cpu_count() or 4

    src_dir = Path(src_dir)
    bin_dir = Path(bin_dir)

    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    makefile = src_dir / "Makefile"
    if not makefile.exists():
        raise FileNotFoundError(f"Makefile not found: {makefile}")

    print(f"Building StereoGene from {src_dir}...")
    print(f"Using {jobs} parallel jobs")

    result = subprocess.run(
        ["make", "-j", str(jobs)],
        cwd=src_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Build failed!", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"make failed with exit code {result.returncode}")

    bin_dir.mkdir(parents=True, exist_ok=True)

    for name in BINARIES:
        src_bin = src_dir / name
        if not src_bin.exists():
            raise FileNotFoundError(f"Binary not found after build: {src_bin}")
        dst_bin = bin_dir / name
        shutil.copy2(src_bin, dst_bin)
        dst_bin.chmod(0o755)
        print(f"  Installed {name}")

    print("Build complete!")


def clean(src_dir: Path | None = None) -> None:
    """Run make clean in the source directory."""
    if src_dir is None:
        src_dir = get_src_dir()
    subprocess.run(["make", "clean"], cwd=src_dir, check=True)


if __name__ == "__main__":
    build()
