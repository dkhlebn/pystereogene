"""Chromosome file resolution."""

from pathlib import Path

_BUNDLED = {
    "hg18": "hg18_chrom",
    "hg19": "hg19_chrom",
}


def _get_bundled_chrom_dir() -> Path:
    """Get the directory containing bundled chromosome files."""
    return Path(__file__).parent / "_vendor" / "src"


def resolve_chrom(genome_or_path: str | Path) -> Path:
    """
    Resolve a chromosome file path or genome shortcut.

    Args:
        genome_or_path: Either a genome shortcut ("hg18", "hg19") or a path to
            a chromosome lengths file.

    Returns:
        Absolute path to the chromosome file.

    Raises:
        ValueError: If the genome shortcut is not recognized and no file exists.
        FileNotFoundError: If the specified file does not exist.

    Example:
        >>> resolve_chrom("hg19")
        PosixPath('/path/to/pystereogene/_vendor/src/hg19_chrom')
        >>> resolve_chrom("/path/to/hg38.chrom")
        PosixPath('/path/to/hg38.chrom')
    """
    key = str(genome_or_path)

    if key in _BUNDLED:
        bundled_dir = _get_bundled_chrom_dir()
        chrom_file = bundled_dir / _BUNDLED[key]
        if chrom_file.exists():
            return chrom_file
        raise FileNotFoundError(
            f"Bundled chromosome file for {key} not found at {chrom_file}. "
            "Ensure the package was installed correctly."
        )

    if key == "hg38":
        raise ValueError(
            "hg38 is not bundled. Download from:\n"
            "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chrom.sizes"
        )

    path = Path(genome_or_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Chromosome file not found: {path}")
    return path


def list_bundled() -> list[str]:
    """List available bundled genome shortcuts."""
    return list(_BUNDLED.keys())
