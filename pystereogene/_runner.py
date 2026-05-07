"""Common runner infrastructure for StereoGene binaries."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from pystereogene._bin import get_binary
from pystereogene.chrom import resolve_chrom
from pystereogene.exceptions import StereoGeneError
from pystereogene.params import PARAM_MAP, format_value

MAX_FILES = 1024


def setup_workdir(
    workdir: str | Path | None,
    cache_dir: str | Path | None = None,
) -> tuple[Path, bool]:
    """
    Set up the working directory structure.

    Args:
        workdir: User-provided working directory, or None for temp.
        cache_dir: Optional persistent cache directory for profiles.

    Returns:
        Tuple of (workdir_path, is_temp) where is_temp indicates if cleanup is needed.
    """
    if workdir is None:
        workdir = Path(tempfile.mkdtemp(prefix="psg_"))
        is_temp = True
    else:
        workdir = Path(workdir).expanduser().resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        is_temp = False

    (workdir / "tracks").mkdir(exist_ok=True)
    (workdir / "res").mkdir(exist_ok=True)

    if cache_dir is not None:
        cache_dir = Path(cache_dir).expanduser().resolve()
        cache_dir.mkdir(parents=True, exist_ok=True)
        profiles_dir = cache_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)
        version_file = cache_dir / "CACHE_VERSION"
        if version_file.exists():
            cached_version = version_file.read_text().strip()
            if cached_version != "2.51":
                raise StereoGeneError(
                    f"StereoGene version mismatch in cache. Expected 2.51, found {cached_version}. "
                    f"Delete cache directory and re-run: rm -rf {cache_dir}"
                )
        else:
            version_file.write_text("2.51\n")
    else:
        profiles_dir = workdir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

    return workdir, is_temp


def stage_tracks(
    tracks: list[str | Path],
    workdir: Path,
) -> list[str]:
    """
    Stage input track files as symlinks in the workdir.

    Args:
        tracks: List of track file paths.
        workdir: Working directory.

    Returns:
        List of staged filenames (just the basename, for CLI).

    Raises:
        FileNotFoundError: If a track file doesn't exist.
        ValueError: If too many tracks are provided or basenames collide.
    """
    if len(tracks) > MAX_FILES:
        raise ValueError(f"Too many input files: {len(tracks)} > {MAX_FILES}")

    tracks_dir = workdir / "tracks"
    staged = []
    seen_basenames: dict[str, Path] = {}

    for track in tracks:
        track = Path(track).expanduser().resolve()
        if not track.exists():
            raise FileNotFoundError(f"Track file not found: {track}")

        basename = track.name
        if basename in seen_basenames:
            raise ValueError(
                f"Duplicate track: '{basename}' appears multiple times.\n"
                f"  First: {seen_basenames[basename]}\n"
                f"  Again: {track}\n"
                f"Remove duplicates or rename files if they differ."
            )
        seen_basenames[basename] = track

        link = tracks_dir / basename
        if link.exists():
            # Don't delete the user's file if it's already in the staging dir
            if link.resolve() == track:
                staged.append(basename)
                continue
            link.unlink()
        link.symlink_to(track)
        staged.append(basename)

    return staged


def write_config(
    workdir: Path,
    chrom_path: Path,
    cache_dir: Path | None,
    extra_params: dict[str, Any],
) -> Path:
    """
    Write the StereoGene config file.

    Args:
        workdir: Working directory.
        chrom_path: Path to chromosome file.
        cache_dir: Optional cache directory for profiles.
        extra_params: Additional parameters from kwargs.

    Returns:
        Path to the config file.
    """
    cfg_path = workdir / "run.cfg"
    prof_path = (
        Path(cache_dir).expanduser().resolve() / "profiles"
        if cache_dir
        else workdir / "profiles"
    )

    lines = [
        f"trackPath = {workdir / 'tracks'}/",
        f"profPath = {prof_path}/",
        f"resPath = {workdir / 'res'}/",
        f"statistics = {workdir / 'res' / 'statistics'}",
        f"params = {workdir / 'res' / 'params'}",
        f"log = {workdir / 'stereogene.log'}",
        f"chrom = {chrom_path}",
    ]

    for py_name, value in extra_params.items():
        if value is None:
            continue
        cli_name = PARAM_MAP.get(py_name, py_name)
        lines.append(f"{cli_name} = {format_value(value)}")

    cfg_path.write_text("\n".join(lines) + "\n")
    return cfg_path


def run_binary(
    binary_name: str,
    cfg_path: Path,
    track_args: list[str],
    workdir: Path,
    extra_cli_args: list[str] | None = None,
) -> subprocess.CompletedProcess:
    """
    Run a StereoGene binary.

    Args:
        binary_name: Name of the binary to run.
        cfg_path: Path to the config file.
        track_args: Track file arguments.
        workdir: Working directory.
        extra_cli_args: Additional CLI arguments.

    Returns:
        CompletedProcess object.

    Raises:
        StereoGeneError: If the binary exits with an error.
    """
    binary = get_binary(binary_name)
    cmd = [binary, f"cfg={cfg_path}"]

    if extra_cli_args:
        cmd.extend(extra_cli_args)

    cmd.extend(track_args)

    result = subprocess.run(
        cmd,
        cwd=workdir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        stderr_tail = "\n".join(result.stderr.splitlines()[-20:]) if result.stderr else ""
        raise StereoGeneError(
            f"{binary_name} failed with exit code {result.returncode}\n"
            f"Command: {' '.join(cmd)}\n"
            f"Stderr:\n{stderr_tail}"
        )

    return result


def cleanup_workdir(workdir: Path, is_temp: bool, keep: bool) -> None:
    """Clean up the working directory if appropriate."""
    if is_temp and not keep:
        shutil.rmtree(workdir, ignore_errors=True)


def check_log_for_warnings(workdir: Path) -> bool:
    """Check the StereoGene log file for warnings or errors."""
    log_file = workdir / "stereogene.log"
    if not log_file.exists():
        return False
    content = log_file.read_text()
    return bool(re.search(r"\b(error|Warning)\b", content, re.IGNORECASE))


def parse_stdout_pairs(stdout: str) -> list[dict]:
    """
    Parse StereoGene stdout to extract per-pair results.

    Format:
        in1="track1"
        in2="track2"
        out="path"

        Correlation=0.328
        bg_cc0.001
        p-val=1.23e-10
        nWindows=1234
        =================================

    Returns:
        List of dicts with keys: track1, track2, fg_corr, bg_corr, p_value, n_fg.
        Values may be math.nan if the C++ emitted NA (e.g., nWindows=0).
    """
    import math

    pairs = []
    blocks = stdout.split("=================================")

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        pair: dict[str, Any] = {}

        m = re.search(r'in1="([^"]+)"', block)
        if m:
            pair["track1"] = m.group(1)

        m = re.search(r'in2="([^"]+)"', block)
        if m:
            pair["track2"] = m.group(1)

        m = re.search(r"Correlation=([\d.e+-]+|NA)", block)
        if m:
            val = m.group(1)
            pair["fg_corr"] = math.nan if val == "NA" else float(val)

        m = re.search(r"bg_cc=?([\d.e+-]+|NA)", block)
        if m:
            val = m.group(1)
            pair["bg_corr"] = math.nan if val == "NA" else float(val)

        m = re.search(r"p-val=([\d.e+-]+|NA)", block)
        if m:
            val = m.group(1)
            pair["p_value"] = math.nan if val == "NA" else float(val)

        m = re.search(r"nWindows=(\d+)", block)
        if m:
            pair["n_fg"] = int(m.group(1))

        if "track1" in pair and "track2" in pair:
            pairs.append(pair)

    return pairs
