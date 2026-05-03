"""ParseGenes function for extracting gene features."""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from pystereogene._bin import get_binary
from pystereogene.exceptions import StereoGeneError

import subprocess


@dataclass
class ParseGenesResult:
    """Result from parse_genes() call."""

    gene: Path
    gene_beg: Path
    gene_end: Path
    exon: Path
    exon_beg: Path
    exon_end: Path
    intron: Path
    intron_beg: Path
    intron_end: Path
    workdir: Path


def parse_genes(
    annotation: str | Path,
    *,
    track_dir: str | Path | None = None,
    gencode_level: int = 2,
    biotypes: str | list[str] | None = None,
    keep_workdir: bool = False,
) -> ParseGenesResult:
    """
    Parse a GTF/GFF or BED12 file to extract gene features.

    Creates 9 BED files containing genes, exons, and introns with their
    start and end points.

    Note:
        ParseGenes does NOT use the standard config file mechanism.
        It calls parseArgs() directly instead of initSG().

    Args:
        annotation: Path to GTF (GENCODE format) or BED12 (RefSeq format) file.
        track_dir: Output directory for BED files. If None, uses a temp directory.
        gencode_level: GENCODE confidence level filter (1, 2, or 3). Default 2.
        biotypes: Gene biotypes to include (e.g., "protein_coding,lncRNA").
            Can be a string or list. If None, includes all biotypes.
        keep_workdir: If True, don't delete the working directory after completion.

    Returns:
        ParseGenesResult containing paths to all 9 output BED files:
            - gene, gene_beg, gene_end: Gene bodies and boundaries
            - exon, exon_beg, exon_end: Exon bodies and boundaries
            - intron, intron_beg, intron_end: Intron bodies and boundaries

    Raises:
        StereoGeneError: If ParseGenes exits with an error.
        FileNotFoundError: If annotation file not found.

    Example:
        >>> import pystereogene as psg
        >>> result = psg.parse_genes(
        ...     "gencode.v38.annotation.gtf",
        ...     gencode_level=2,
        ...     biotypes=["protein_coding", "lncRNA"],
        ... )
        >>> # Use gene starts as a track for correlation analysis
        >>> corr = psg.stereoGene([result.gene_beg, "H3K4me3.bed"], "hg38.chrom")
    """
    annotation_path = Path(annotation).expanduser().resolve()
    if not annotation_path.exists():
        raise FileNotFoundError(f"Annotation file not found: {annotation_path}")

    if track_dir is None:
        track_dir = Path(tempfile.mkdtemp(prefix="psg_pg_"))
        is_temp = True
    else:
        track_dir = Path(track_dir).expanduser().resolve()
        track_dir.mkdir(parents=True, exist_ok=True)
        is_temp = False

    try:
        binary = get_binary("ParseGenes")

        cmd = [binary, f"trackPath={track_dir}/"]

        if gencode_level != 2:
            cmd.append(f"gencodeLevel={gencode_level}")

        if biotypes:
            if isinstance(biotypes, list):
                biotypes = ",".join(biotypes)
            cmd.append(f"biotypes={biotypes}")

        cmd.append(str(annotation_path))

        result = subprocess.run(
            cmd,
            cwd=track_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            stderr_tail = "\n".join(result.stderr.splitlines()[-20:]) if result.stderr else ""
            raise StereoGeneError(
                f"ParseGenes failed with exit code {result.returncode}\n"
                f"Command: {' '.join(cmd)}\n"
                f"Stderr:\n{stderr_tail}"
            )

        stem = annotation_path.stem
        if stem.endswith(".gtf") or stem.endswith(".gff"):
            stem = Path(stem).stem

        return ParseGenesResult(
            gene=track_dir / f"{stem}_gene.bed",
            gene_beg=track_dir / f"{stem}_g_beg.bed",
            gene_end=track_dir / f"{stem}_g_end.bed",
            exon=track_dir / f"{stem}_exn.bed",
            exon_beg=track_dir / f"{stem}_e_beg.bed",
            exon_end=track_dir / f"{stem}_e_end.bed",
            intron=track_dir / f"{stem}_ivs.bed",
            intron_beg=track_dir / f"{stem}_i_beg.bed",
            intron_end=track_dir / f"{stem}_i_end.bed",
            workdir=track_dir,
        )

    except Exception:
        if is_temp and not keep_workdir:
            import shutil

            shutil.rmtree(track_dir, ignore_errors=True)
        raise
