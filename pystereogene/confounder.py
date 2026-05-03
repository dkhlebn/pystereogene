"""Confounder function for computing confounder tracks."""

import shutil
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
class ConfounderResult:
    """Result from confounder() call."""

    bgraph_file: Path
    covar_file: Path
    bprof_file: Path | None
    workdir: Path
    log_file: Path
    warnings: bool = False


def confounder(
    tracks: list[str | Path],
    chrom: str | Path,
    *,
    workdir: str | Path | None = None,
    keep_workdir: bool = False,
    **kwargs: Any,
) -> ConfounderResult:
    """
    Compute a confounder track from multiple input tracks.

    The confounder is the first principal component of the input tracks,
    useful for partial correlation analysis to remove shared variance.

    Args:
        tracks: List of track file paths to compute confounder from.
        chrom: Path to chromosome lengths file, or genome shortcut ("hg18", "hg19").
        workdir: Working directory for output. If None, uses a temp directory.
        keep_workdir: If True, don't delete the working directory after completion.
        **kwargs: Additional parameters passed to Confounder.

    Returns:
        ConfounderResult containing:
            - bgraph_file: Path to the confounder bedGraph track
            - covar_file: Path to the covariance matrix file
            - bprof_file: Path to the binary profile (if exists)
            - workdir: Path to the working directory
            - log_file: Path to the StereoGene log
            - warnings: True if the log contains warnings/errors

    Raises:
        StereoGeneError: If Confounder exits with an error.
        FileNotFoundError: If track or chrom file not found.

    Example:
        >>> import pystereogene as psg
        >>> result = psg.confounder(
        ...     ["H3K4me3.bed", "H3K27me3.bed", "H3K36me3.bed"],
        ...     chrom="hg38.chrom",
        ... )
        >>> print(f"Confounder track: {result.bgraph_file}")
        >>> # Use with project() to remove confounder effect
        >>> proj = psg.project(["track.bed"], "hg38.chrom", result.bgraph_file)
    """
    chrom_path = resolve_chrom(chrom)
    wd, is_temp = setup_workdir(workdir, None)

    try:
        staged = stage_tracks(tracks, wd)
        cfg_path = write_config(wd, chrom_path, None, kwargs)

        run_binary("Confounder", cfg_path, staged, wd)

        bgraph_file, covar_file, bprof_file = _find_confounder_outputs(wd)
        warnings = check_log_for_warnings(wd)

        return ConfounderResult(
            bgraph_file=bgraph_file,
            covar_file=covar_file,
            bprof_file=bprof_file,
            workdir=wd,
            log_file=wd / "stereogene.log",
            warnings=warnings,
        )

    except Exception:
        cleanup_workdir(wd, is_temp, keep_workdir)
        raise


def _find_confounder_outputs(workdir: Path) -> tuple[Path, Path, Path | None]:
    """Find confounder output files and move them to res/."""
    tracks_dir = workdir / "tracks"
    res_dir = workdir / "res"
    profiles_dir = workdir / "profiles"

    bgraph_file = tracks_dir / "confounder.bgraph"
    if not bgraph_file.exists():
        raise FileNotFoundError(f"Confounder bgraph not found: {bgraph_file}")

    covar_file_src = workdir / "confounder.covar"
    covar_file_dst = res_dir / "confounder.covar"

    if covar_file_src.exists():
        shutil.copy2(covar_file_src, covar_file_dst)
    elif not covar_file_dst.exists():
        raise FileNotFoundError(f"Confounder covar not found: {covar_file_src}")

    bprof_file = profiles_dir / "confounder.bprof"
    if not bprof_file.exists():
        bprof_file = None

    return bgraph_file, covar_file_dst, bprof_file
