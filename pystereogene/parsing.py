"""Output file parsers for StereoGene results."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd


def _require_pandas():
    """Import pandas or raise ImportError with a helpful message."""
    try:
        import pandas as pd

        return pd
    except ImportError:
        raise ImportError(
            "pandas is required for this function. "
            "Install with: pip install pystereogene[full]"
        ) from None


def parse_fg(path: Path | str) -> np.ndarray:
    """
    Parse a .fg foreground correlation file (SHORT format).

    Args:
        path: Path to the .fg file.

    Returns:
        1-D numpy array of correlation values.
    """
    path = Path(path)
    values = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split()
                if len(parts) == 1:
                    values.append(float(parts[0]))
                else:
                    break
    return np.array(values, dtype=np.float64)


def parse_fg_detail(path: Path | str) -> "pd.DataFrame":
    """
    Parse a .fg foreground correlation file (DETAIL format).

    Args:
        path: Path to the .fg file.

    Returns:
        DataFrame with columns: chrom, start, end, corr
    """
    pd = _require_pandas()
    return pd.read_csv(
        path,
        sep=r"\s+",
        names=["chrom", "start", "end", "corr"],
        comment="#",
    )


def parse_bkg(path: Path | str) -> np.ndarray:
    """
    Parse a .bkg background correlation file.

    Args:
        path: Path to the .bkg file.

    Returns:
        1-D numpy array of correlation values.
    """
    return parse_fg(path)


def parse_dist(path: Path | str) -> "pd.DataFrame":
    """
    Parse a .dist cross-correlation file.

    Args:
        path: Path to the .dist file.

    Returns:
        DataFrame with columns: dist, Bkg, Fg, FgPlus, FgMinus (+ optional chr columns)
    """
    pd = _require_pandas()
    return pd.read_csv(path, sep=r"\s+", comment="#")


def parse_bgraph(path: Path | str) -> "pd.DataFrame":
    """
    Parse a .bgraph bedGraph file (local correlation track).

    Args:
        path: Path to the .bgraph file.

    Returns:
        DataFrame with columns: chrom, start, end, value
    """
    pd = _require_pandas()
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("track") or line.startswith("#") or not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                rows.append(
                    {
                        "chrom": parts[0],
                        "start": int(parts[1]),
                        "end": int(parts[2]),
                        "value": float(parts[3]),
                    }
                )
    return pd.DataFrame(rows)


def parse_auto(path: Path | str) -> "pd.DataFrame":
    """
    Parse a .auto autocorrelation file.

    Args:
        path: Path to the .auto file.

    Returns:
        DataFrame with columns: dist, autocorr
    """
    pd = _require_pandas()
    return pd.read_csv(
        path,
        sep=r"\s+",
        names=["dist", "autocorr"],
        comment="#",
    )


def parse_spect(path: Path | str) -> "pd.DataFrame":
    """
    Parse a .spect spectrum file.

    Args:
        path: Path to the .spect file.

    Returns:
        DataFrame with columns: Wave_Length, Spectrum1, Spectrum2
    """
    pd = _require_pandas()
    return pd.read_csv(path, sep=r"\s+", comment="#")


def parse_lchist(path: Path | str) -> "pd.DataFrame":
    """
    Parse a .LChist local correlation histogram file.

    Args:
        path: Path to the .LChist file.

    Returns:
        DataFrame with 11 columns: corr, obs, nObs, exp, nExp, r_CDF_obs,
        r_CDF_exp, R_FDR, l_CDF_obs, l_CDF_exp, L_FDR
    """
    pd = _require_pandas()
    return pd.read_csv(path, sep=r"\s+", comment="#")


def parse_statistics(path: Path | str) -> "pd.DataFrame":
    """
    Parse a statistics.tsv file.

    Args:
        path: Path to the statistics.tsv file.

    Returns:
        DataFrame with all statistics columns.
    """
    pd = _require_pandas()
    return pd.read_csv(path, sep="\t")


def parse_params(path: Path | str) -> "pd.DataFrame":
    """
    Parse a params.tsv file.

    Args:
        path: Path to the params.tsv file.

    Returns:
        DataFrame with all parameter columns.
    """
    pd = _require_pandas()
    return pd.read_csv(path, sep="\t")


def parse_covar(path: Path | str) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Parse a .covar covariance matrix file from Confounder.

    Args:
        path: Path to the .covar file.

    Returns:
        Tuple of (covariance_matrix NxN, eigenvector N, eigenvalue).
    """
    path = Path(path)
    lines = path.read_text().strip().split("\n")

    header = lines[0].split("\t")[1:]
    n = len(header)

    matrix = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        row_parts = lines[i + 1].split("\t")[1:]
        for j, val in enumerate(row_parts):
            matrix[i, j] = float(val)

    eigenvector = np.zeros(n, dtype=np.float64)
    eigenvalue = 0.0

    for line in lines[n + 1 :]:
        if line.startswith("eigenVector"):
            parts = line.split("=")[1].strip().split()
            for i, val in enumerate(parts):
                eigenvector[i] = float(val)
        elif line.startswith("eigenValue"):
            m = re.search(r"eigenValue=([\d.e+-]+)", line)
            if m:
                eigenvalue = float(m.group(1))

    return matrix, eigenvector, eigenvalue


def parse_projections_log(path: Path | str) -> "pd.DataFrame":
    """
    Parse a projections log file from Projector.

    Args:
        path: Path to the projections file.

    Returns:
        DataFrame with columns: track, minVal, maxVal, e, proj_coef
    """
    pd = _require_pandas()
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("confounder=") or line.startswith("track\t"):
                continue
            if line.startswith("<"):
                m = re.match(r"<([^>]+)>\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s+z=([\d.e+-]+)", line)
                if m:
                    rows.append(
                        {
                            "track": m.group(1),
                            "minVal": float(m.group(2)),
                            "maxVal": float(m.group(3)),
                            "e": float(m.group(4)),
                            "proj_coef": float(m.group(5)),
                        }
                    )
    return pd.DataFrame(rows)
