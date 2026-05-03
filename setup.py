"""Setup script for pystereogene with custom build_ext to compile C++ binaries."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

BINARIES = ["StereoGene", "Smoother", "Binner", "Projector", "Confounder", "ParseGenes"]


class _FakeExtension(Extension):
    """Fake extension to trigger build_ext."""

    def __init__(self):
        super().__init__("_fake", sources=[])


class BuildStereoGene(build_ext):
    """Custom build_ext to compile StereoGene C++ binaries."""

    def run(self):
        src_dir = Path(__file__).parent / "pystereogene" / "_vendor" / "src"
        bin_dir = Path(__file__).parent / "pystereogene" / "_vendor" / "bin"

        if not src_dir.exists():
            print(f"Warning: Source directory not found: {src_dir}")
            print("Skipping C++ build - binaries must be provided separately")
            return

        makefile = src_dir / "Makefile"
        if not makefile.exists():
            print(f"Warning: Makefile not found: {makefile}")
            print("Skipping C++ build - binaries must be provided separately")
            return

        jobs = os.cpu_count() or 4
        print(f"Building StereoGene from {src_dir} with {jobs} parallel jobs...")

        result = subprocess.run(
            ["make", "-j", str(jobs)],
            cwd=src_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("Build output:", result.stdout, file=sys.stderr)
            print("Build errors:", result.stderr, file=sys.stderr)
            raise RuntimeError(f"make failed with exit code {result.returncode}")

        bin_dir.mkdir(parents=True, exist_ok=True)

        for name in BINARIES:
            src_bin = src_dir / name
            if src_bin.exists():
                dst_bin = bin_dir / name
                shutil.copy2(src_bin, dst_bin)
                dst_bin.chmod(0o755)
                print(f"  Installed {name}")
            else:
                print(f"  Warning: {name} not found after build")

        print("Build complete!")

    def build_extension(self, ext):
        pass


setup(
    ext_modules=[_FakeExtension()],
    cmdclass={"build_ext": BuildStereoGene},
)
