"""Main StereoGene correlation function."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pystereogene._runner import (
    check_log_for_warnings,
    cleanup_workdir,
    parse_stdout_pairs,
    run_binary,
    setup_workdir,
    stage_tracks,
    write_config,
)
from pystereogene.chrom import resolve_chrom


@dataclass
class PairResult:
    """Result for a single track pair correlation."""

    track1: str
    track2: str
    fg_corr: float
    bg_corr: float
    p_value: float
    n_fg: int
    fg_corr_sd: float = 0.0
    bg_corr_sd: float = 0.0
    mann_z: float = 0.0
    n_bg: int = 0
    files: dict[str, Path] = field(default_factory=dict)


@dataclass
class StereoGeneResult:
    """Result from stereoGene() call."""

    pairs: list[PairResult]
    workdir: Path
    log_file: Path
    warnings: bool = False


def stereoGene(
    tracks: list[str | Path],
    chrom: str | Path,
    *,
    workdir: str | Path | None = None,
    cache_dir: str | Path | None = None,
    keep_workdir: bool = False,
    **kwargs: Any,
) -> StereoGeneResult:
    """
    Compute kernel correlation between genomic tracks.

    This is the main StereoGene function. It computes pairwise correlations
    between all input tracks using kernel convolution and FFT.

    Args:
        tracks: List of track file paths (BED, WIG, bedGraph, BroadPeak, NarrowPeak, or .mod).
            With N tracks, produces N*(N-1)/2 pair comparisons.
        chrom: Path to chromosome lengths file, or genome shortcut ("hg18", "hg19").
        workdir: Working directory for output. If None, uses a temp directory.
        cache_dir: Persistent directory for profile cache. If None, profiles go in workdir.
        keep_workdir: If True, don't delete the working directory after completion.
        **kwargs: Additional parameters passed to StereoGene. Common options:
            - bin (int): Bin size in bp (default 100)
            - kernel_sigma (int): Kernel width in bp (default 1000)
            - w_size (int): Window size in bp (default 100000)
            - auto_corr (bool): Compute autocorrelation (default False)
            - cross (bool): Compute cross-correlation (default True)
            - out_lc (str): Local correlation output ("0", "BASE", "CENTER")
            - write_distr (str): Distribution format ("NONE", "SHORT", "DETAIL")

    Returns:
        StereoGeneResult containing:
            - pairs: List of PairResult with correlation statistics
            - workdir: Path to the working directory
            - log_file: Path to the StereoGene log
            - warnings: True if the log contains warnings/errors

    Raises:
        StereoGeneError: If StereoGene exits with an error.
        FileNotFoundError: If track or chrom file not found.
        ValueError: If too many tracks (>1024) are provided.

    Example:
        >>> import pystereogene as psg
        >>> result = psg.stereoGene(
        ...     ["H3K4me3.bed", "H3K27me3.bed"],
        ...     chrom="hg38.chrom",
        ...     kernel_sigma=2000,
        ...     auto_corr=True,
        ... )
        >>> for pair in result.pairs:
        ...     print(f"{pair.track1} vs {pair.track2}: KC={pair.fg_corr:.3f}, p={pair.p_value:.2e}")

    Note:
        For parallel execution across many track pairs, use ProcessPoolExecutor,
        NOT ThreadPoolExecutor. StereoGene uses global state internally.
    """
    chrom_path = resolve_chrom(chrom)
    wd, is_temp = setup_workdir(workdir, cache_dir)

    try:
        staged = stage_tracks(tracks, wd)
        cfg_path = write_config(wd, chrom_path, cache_dir, kwargs)

        result = run_binary("StereoGene", cfg_path, staged, wd)

        pairs = _build_pair_results(result.stdout, wd)
        warnings = check_log_for_warnings(wd)

        return StereoGeneResult(
            pairs=pairs,
            workdir=wd,
            log_file=wd / "stereogene.log",
            warnings=warnings,
        )

    except Exception:
        cleanup_workdir(wd, is_temp, keep_workdir)
        raise

    finally:
        if not keep_workdir and is_temp:
            pass


def _build_pair_results(stdout: str, workdir: Path) -> list[PairResult]:
    """Build PairResult objects from stdout and output files."""
    parsed = parse_stdout_pairs(stdout)
    res_dir = workdir / "res"

    stats_file = res_dir / "statistics.tsv"
    stats_rows = _parse_statistics_tsv(stats_file) if stats_file.exists() else {}

    results = []
    for p in parsed:
        track1 = p.get("track1", "")
        track2 = p.get("track2", "")
        stem = f"{track1}~{track2}"

        files = _find_output_files(res_dir, stem, track1)

        stats = stats_rows.get((track1, track2), {})

        results.append(
            PairResult(
                track1=track1,
                track2=track2,
                fg_corr=p.get("fg_corr", 0.0),
                bg_corr=p.get("bg_corr", 0.0),
                p_value=p.get("p_value", 1.0),
                n_fg=p.get("n_fg", 0),
                fg_corr_sd=stats.get("FgCorr_sd", 0.0),
                bg_corr_sd=stats.get("BgCorr_sd", 0.0),
                mann_z=stats.get("Mann-Z", 0.0),
                n_bg=stats.get("nBkg", 0),
                files=files,
            )
        )

    return results


def _find_output_files(res_dir: Path, stem: str, track1: str) -> dict[str, Path]:
    """Find all output files for a pair."""
    files: dict[str, Path] = {}
    extensions = ["fg", "bkg", "dist", "bgraph", "LChist", "spect", "r"]

    for ext in extensions:
        path = res_dir / f"{stem}.{ext}"
        if path.exists():
            files[ext] = path

    auto_path = res_dir / f"{track1}.auto"
    if auto_path.exists():
        files["auto"] = auto_path

    return files


def _parse_statistics_tsv(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    """Parse statistics.tsv into a dict keyed by (name1, name2)."""
    rows: dict[tuple[str, str], dict[str, Any]] = {}

    with open(path) as f:
        header = f.readline().strip().split("\t")
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < len(header):
                continue
            row = dict(zip(header, parts))

            name1 = row.get("name1", "")
            name2 = row.get("name2", "")

            parsed_row: dict[str, Any] = {}
            for key, val in row.items():
                try:
                    if "." in val or "e" in val.lower():
                        parsed_row[key] = float(val)
                    else:
                        parsed_row[key] = int(val)
                except ValueError:
                    parsed_row[key] = val

            rows[(name1, name2)] = parsed_row

    return rows
