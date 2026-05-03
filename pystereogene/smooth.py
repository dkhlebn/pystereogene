"""Smoother function for track smoothing."""

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
class SmoothResult:
    """Result from smooth() call."""

    output_files: list[Path]
    workdir: Path
    log_file: Path
    warnings: bool = False


def smooth(
    tracks: list[str | Path],
    chrom: str | Path,
    *,
    workdir: str | Path | None = None,
    keep_workdir: bool = False,
    **kwargs: Any,
) -> SmoothResult:
    """
    Smooth genomic tracks using kernel convolution.

    Applies a smoothing kernel to each input track and outputs smoothed
    bedGraph files.

    Args:
        tracks: List of track file paths to smooth.
        chrom: Path to chromosome lengths file, or genome shortcut ("hg18", "hg19").
        workdir: Working directory for output. If None, uses a temp directory.
        keep_workdir: If True, don't delete the working directory after completion.
        **kwargs: Additional parameters passed to Smoother. Common options:
            - kernel_sigma (int): Smoothing kernel width in bp (default 1000)
            - smooth_z (float): Z-score threshold for output
            - bin (int): Bin size in bp (default 100)

    Returns:
        SmoothResult containing:
            - output_files: List of output .bgr files (one per input track)
            - workdir: Path to the working directory
            - log_file: Path to the StereoGene log
            - warnings: True if the log contains warnings/errors

    Raises:
        StereoGeneError: If Smoother exits with an error.
        FileNotFoundError: If track or chrom file not found.

    Example:
        >>> import pystereogene as psg
        >>> result = psg.smooth(
        ...     ["H3K4me3.bed", "H3K27me3.bed"],
        ...     chrom="hg38.chrom",
        ...     kernel_sigma=2000,
        ... )
        >>> for f in result.output_files:
        ...     print(f"Smoothed: {f}")
    """
    chrom_path = resolve_chrom(chrom)
    wd, is_temp = setup_workdir(workdir, None)

    try:
        staged = stage_tracks(tracks, wd)
        cfg_path = write_config(wd, chrom_path, None, kwargs)

        run_binary("Smoother", cfg_path, staged, wd)

        output_files = _find_smooth_outputs(wd, tracks)
        warnings = check_log_for_warnings(wd)

        return SmoothResult(
            output_files=output_files,
            workdir=wd,
            log_file=wd / "stereogene.log",
            warnings=warnings,
        )

    finally:
        if not keep_workdir:
            cleanup_workdir(wd, is_temp, keep=False)


def _find_smooth_outputs(workdir: Path, tracks: list[str | Path]) -> list[Path]:
    """Find smoothed output files."""
    outputs = []
    tracks_dir = workdir / "tracks"

    for track in tracks:
        stem = Path(track).stem
        smooth_file = tracks_dir / f"{stem}_sm.bgr"
        if smooth_file.exists():
            outputs.append(smooth_file)

    return outputs
