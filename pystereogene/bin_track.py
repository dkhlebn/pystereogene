"""Binner function for track binning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pystereogene._runner import (
    check_log_for_warnings,
    cleanup_workdir,
    run_binary,
    setup_workdir,
    stage_tracks,
    write_config,
)
from pystereogene.chrom import resolve_chrom


@dataclass
class BinResult:
    """Result from bin_track() call."""

    output_files: list[Path]
    bin_size: int
    workdir: Path
    log_file: Path
    warnings: bool = False


def bin_track(
    tracks: list[str | Path],
    chrom: str | Path,
    *,
    workdir: str | Path | None = None,
    keep_workdir: bool = False,
    bin: int = 100,
    **kwargs: Any,
) -> BinResult:
    """
    Bin genomic tracks into fixed-width bins.

    Creates binned bedGraph files from input tracks.

    Args:
        tracks: List of track file paths to bin.
        chrom: Path to chromosome lengths file, or genome shortcut ("hg18", "hg19").
        workdir: Working directory for output. If None, uses a temp directory.
        keep_workdir: If True, don't delete the working directory after completion.
        bin: Bin size in base pairs (default 100).
        **kwargs: Additional parameters passed to Binner.

    Returns:
        BinResult containing:
            - output_files: List of output .bgr files (one per input track)
            - bin_size: The bin size used
            - workdir: Path to the working directory
            - log_file: Path to the StereoGene log
            - warnings: True if the log contains warnings/errors

    Raises:
        StereoGeneError: If Binner exits with an error.
        FileNotFoundError: If track or chrom file not found.

    Example:
        >>> import pystereogene as psg
        >>> result = psg.bin_track(
        ...     ["H3K4me3.bed"],
        ...     chrom="hg38.chrom",
        ...     bin=200,
        ... )
        >>> print(f"Binned file: {result.output_files[0]}")
    """
    chrom_path = resolve_chrom(chrom)
    wd, is_temp = setup_workdir(workdir, None)

    kwargs["bin"] = bin

    try:
        staged = stage_tracks(tracks, wd)
        cfg_path = write_config(wd, chrom_path, None, kwargs)

        run_binary("Binner", cfg_path, staged, wd)

        output_files = _find_bin_outputs(wd, tracks, bin)
        warnings = check_log_for_warnings(wd)

        return BinResult(
            output_files=output_files,
            bin_size=bin,
            workdir=wd,
            log_file=wd / "stereogene.log",
            warnings=warnings,
        )

    finally:
        if not keep_workdir:
            cleanup_workdir(wd, is_temp, keep=False)


def _find_bin_outputs(workdir: Path, tracks: list[str | Path], bin_size: int) -> list[Path]:
    """Find binned output files."""
    outputs = []
    tracks_dir = workdir / "tracks"

    for track in tracks:
        stem = Path(track).stem
        bin_file = tracks_dir / f"{stem}_{bin_size}.bgr"
        if bin_file.exists():
            outputs.append(bin_file)

    return outputs
