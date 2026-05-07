"""
pystereogene - Python wrapper for StereoGene genome-wide correlation analysis.

Usage:
    import pystereogene as psg

    result = psg.stereoGene(
        ["track1.bed", "track2.bed"],
        chrom="hg38.chrom",
    )
    print(result.pairs[0].fg_corr, result.pairs[0].p_value)
"""

from pystereogene.correlate import stereoGene, StereoGeneResult, PairResult
from pystereogene.smooth import smooth, SmoothResult
from pystereogene.bin_track import bin_track, BinResult
from pystereogene.confounder import confounder, ConfounderResult
from pystereogene.project import project, ProjectResult
from pystereogene.parse_genes import parse_genes, ParseGenesResult
from pystereogene.model import ModelFile
from pystereogene.chrom import resolve_chrom
from pystereogene.exceptions import StereoGeneError

__version__ = "2.51.0"
__all__ = [
    "stereoGene",
    "StereoGeneResult",
    "PairResult",
    "smooth",
    "SmoothResult",
    "bin_track",
    "BinResult",
    "confounder",
    "ConfounderResult",
    "project",
    "ProjectResult",
    "parse_genes",
    "ParseGenesResult",
    "ModelFile",
    "resolve_chrom",
    "StereoGeneError",
]
