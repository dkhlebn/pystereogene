"""Parameter constants and enums for StereoGene."""

from enum import Enum


class BpType(str, Enum):
    """BroadPeak/NarrowPeak column selector."""

    SCORE = "SCORE"
    SIGNAL = "SIGNAL"
    LOGPVAL = "LOGPVAL"


class KernelType(str, Enum):
    """Kernel type for correlation."""

    NORMAL = "NORMAL"
    LEFT_EXP = "LEFT_EXP"
    RIGHT_EXP = "RIGHT_EXP"


class ComplFg(str, Enum):
    """Strand handling for foreground correlation."""

    IGNORE_STRAND = "IGNORE_STRAND"
    COLLINEAR = "COLLINEAR"
    COMPLEMENT = "COMPLEMENT"


class WriteDistr(str, Enum):
    """Distribution output format."""

    NONE = "NONE"
    SHORT = "SHORT"
    DETAIL = "DETAIL"


class OutRes(str, Enum):
    """Output result format."""

    NONE = "NONE"
    XML = "XML"
    TAB = "TAB"
    BOTH = "BOTH"


class OutLC(str, Enum):
    """Local correlation output mode."""

    OFF = "0"
    BASE = "BASE"
    CENTER = "CENTER"


class LCScale(str, Enum):
    """Local correlation scale."""

    LOG = "LOG"
    LIN = "LIN"


class PlotType(str, Enum):
    """Plot output type."""

    NONE = "NONE"
    R = "R"
    PDF = "PDF"
    HTML = "HTML"
    ALL = "ALL"


PARAM_MAP = {
    "track_path": "trackPath",
    "prof_path": "profPath",
    "res_path": "resPath",
    "statistics_file": "statistics",
    "params_file": "params",
    "log_file": "log",
    "bin_path": "binPath",
    "smooth_path": "smoothPath",
    "aliases": "aliases",
    "bp_type": "bpType",
    "buf_size": "BufSize",
    "bin": "bin",
    "clear": "clear",
    "threshold": "threshold",
    "w_size": "wSize",
    "w_step": "wStep",
    "kernel_type": "kernelType",
    "custom_kern": "customKern",
    "kernel_sigma": "KernelSigma",
    "kernel_shift": "kernelShift",
    "kernel_ns": "kernelNS",
    "compl_fg": "complFg",
    "na": "NA",
    "flank_size": "flankSize",
    "noise_level": "noiseLevel",
    "max_na": "maxNA",
    "max_zero": "maxZero",
    "n_shuffle": "nShuffle",
    "local_shuffle": "localShuffle",
    "out_res": "outRes",
    "out_prj_bgr": "outPrjBGr",
    "out_distr": "outDistr",
    "write_distr": "writeDistr",
    "out_chrom": "outChrom",
    "cross": "Cross",
    "cross_width": "crossWidth",
    "out_spectr": "outSpectr",
    "auto_corr": "AutoCorr",
    "out_lc": "outLC",
    "lc_scale": "LCScale",
    "l_lc": "L_LC",
    "r_lc": "R_LC",
    "plot_type": "plotType",
    "rscript": "Rscript",
    "plot_h": "plotH",
    "plot_w": "plotW",
    "verbose": "verbose",
    "silent": "silent",
    "syntax": "syntax",
    "gencode_level": "gencodeLevel",
    "biotypes": "biotypes",
    "smooth_z": "smoothZ",
    "confounder": "confounder",
}


def python_to_cli(name: str) -> str:
    """Convert Python parameter name to CLI parameter name."""
    return PARAM_MAP.get(name, name)


def format_value(value) -> str:
    """Format a Python value for the config file."""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return ",".join(str(v) for v in value)
    return str(value)
