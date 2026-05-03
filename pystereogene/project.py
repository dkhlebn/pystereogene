"""Projector function for removing confounder effects."""

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
class ProjectResult:
    """Result from project() call."""

    projected_files: list[Path]
    config_file: Path | None
    projections_log: Path | None
    workdir: Path
    log_file: Path
    warnings: bool = False


def project(
    tracks: list[str | Path],
    chrom: str | Path,
    confounder_track: str | Path,
    *,
    workdir: str | Path | None = None,
    keep_workdir: bool = False,
    **kwargs: Any,
) -> ProjectResult:
    """
    Project tracks to remove confounder effect.

    Creates new tracks with the confounder component removed, enabling
    partial correlation analysis.

    Args:
        tracks: List of track file paths to project.
        chrom: Path to chromosome lengths file, or genome shortcut ("hg18", "hg19").
        confounder_track: Path to the confounder bedGraph file (from confounder()).
        workdir: Working directory for output. If None, uses a temp directory.
        keep_workdir: If True, don't delete the working directory after completion.
        **kwargs: Additional parameters passed to Projector.

    Returns:
        ProjectResult containing:
            - projected_files: List of projected bedGraph files
            - config_file: Path to generated config file
            - projections_log: Path to projections log file
            - workdir: Path to the working directory
            - log_file: Path to the StereoGene log
            - warnings: True if the log contains warnings/errors

    Raises:
        StereoGeneError: If Projector exits with an error.
        FileNotFoundError: If track, chrom, or confounder file not found.

    Example:
        >>> import pystereogene as psg
        >>> # First compute confounder
        >>> conf = psg.confounder(["H3K4me3.bed", "H3K27me3.bed"], "hg38.chrom")
        >>> # Then project tracks to remove confounder effect
        >>> proj = psg.project(
        ...     ["track1.bed", "track2.bed"],
        ...     "hg38.chrom",
        ...     conf.bgraph_file,
        ... )
        >>> # Use projected files for partial correlation
        >>> result = psg.stereoGene(proj.projected_files, "hg38.chrom")
    """
    chrom_path = resolve_chrom(chrom)
    confounder_path = Path(confounder_track).expanduser().resolve()

    if not confounder_path.exists():
        raise FileNotFoundError(f"Confounder track not found: {confounder_path}")

    wd, is_temp = setup_workdir(workdir, None)

    try:
        staged = stage_tracks(tracks, wd)

        confounder_link = wd / "tracks" / confounder_path.name
        if not confounder_link.exists():
            confounder_link.symlink_to(confounder_path)

        cfg_path = write_config(wd, chrom_path, None, kwargs)

        extra_cli = [f"confounder={confounder_path.name}"]
        run_binary("Projector", cfg_path, staged, wd, extra_cli_args=extra_cli)

        projected_files, config_file, projections_log = _find_project_outputs(wd, confounder_path)
        warnings = check_log_for_warnings(wd)

        return ProjectResult(
            projected_files=projected_files,
            config_file=config_file,
            projections_log=projections_log,
            workdir=wd,
            log_file=wd / "stereogene.log",
            warnings=warnings,
        )

    except Exception:
        cleanup_workdir(wd, is_temp, keep_workdir)
        raise


def _find_project_outputs(
    workdir: Path, confounder_path: Path
) -> tuple[list[Path], Path | None, Path | None]:
    """Find projector output files."""
    tracks_dir = workdir / "tracks"
    confounder_stem = confounder_path.stem

    proj_dir = tracks_dir / f"{confounder_stem}.proj"
    projected_files = []

    if proj_dir.exists():
        projected_files = sorted(proj_dir.glob("*.bgraph"))

    config_file = workdir / f"{confounder_stem}.cfg"
    if not config_file.exists():
        config_file = None

    projections_log = workdir / "projections"
    if not projections_log.exists():
        projections_log = None

    return projected_files, config_file, projections_log
