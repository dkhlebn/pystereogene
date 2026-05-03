# pystereogene

A Python wrapper for [StereoGene](https://github.com/favorov/stereogene) — a tool for genome-wide correlation analysis of continuous or interval genomic features using kernel convolution and FFT.

## Installation

### From source (development)

```bash
git clone <repo>
cd StereoGene-API
pip install -e .
```

### From PyPI (when published)

```bash
pip install pystereogene
```

### With optional dependencies

```bash
pip install pystereogene[full]  # Adds pandas and matplotlib
```

**System requirements:**
- Linux or macOS (Windows not supported)
- `gcc`/`g++` with C++11 support (for building binaries at install time)
- Python 3.9+

## Quick Start

```python
import pystereogene as psg

# Compute kernel correlation between two tracks
result = psg.stereoGene(
    ["H3K4me3.bed", "H3K27me3.bed"],
    chrom="hg38.chrom",
)

for pair in result.pairs:
    print(f"{pair.track1} vs {pair.track2}:")
    print(f"  Kernel Correlation: {pair.fg_corr:.4f}")
    print(f"  Background Correlation: {pair.bg_corr:.4f}")
    print(f"  Mann-Whitney Z: {pair.mann_z:.2f}")
    print(f"  p-value: {pair.p_value:.2e}")
```

---

## Module Reference

### `pystereogene` (main package)

The top-level package exports all public functions and classes:

```python
import pystereogene as psg

# Functions
psg.stereoGene()      # Main correlation analysis
psg.smooth()          # Track smoothing
psg.bin_track()       # Track binning
psg.confounder()      # Compute confounder track
psg.project()         # Remove confounder effect
psg.parse_genes()     # Parse GTF/BED gene annotations
psg.resolve_chrom()   # Resolve chromosome file path

# Classes
psg.StereoGeneResult  # Result from stereoGene()
psg.PairResult        # Per-pair correlation result
psg.SmoothResult      # Result from smooth()
psg.BinResult         # Result from bin_track()
psg.ConfounderResult  # Result from confounder()
psg.ProjectResult     # Result from project()
psg.ParseGenesResult  # Result from parse_genes()
psg.ModelFile         # Builder for .mod model files
psg.StereoGeneError   # Exception class
```

---

### `pystereogene.correlate`

Main correlation analysis module.

#### `stereoGene(tracks, chrom, **kwargs) → StereoGeneResult`

Compute kernel correlation between genomic tracks.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `tracks` | list[Path] | required | Input track files (BED, WIG, bedGraph, BroadPeak, NarrowPeak, .mod) |
| `chrom` | Path or str | required | Chromosome lengths file, or "hg18"/"hg19" shortcut |
| `workdir` | Path | None | Working directory (temp if None) |
| `cache_dir` | Path | None | Persistent profile cache directory |
| `keep_workdir` | bool | False | Don't delete workdir after completion |
| `bin` | int | 100 | Bin size in bp |
| `kernel_sigma` | int | 1000 | Kernel width in bp |
| `w_size` | int | 100000 | Window size in bp |
| `w_step` | int | 0 | Window step (0 = same as w_size) |
| `kernel_type` | str | "NORMAL" | Kernel type: NORMAL, LEFT_EXP, RIGHT_EXP |
| `auto_corr` | bool | False | Compute autocorrelation |
| `cross` | bool | True | Compute cross-correlation |
| `out_lc` | str | "0" | Local correlation: "0", "BASE", "CENTER" |
| `write_distr` | str | "SHORT" | Distribution output: "NONE", "SHORT", "DETAIL" |
| `n_shuffle` | int | 10000 | Background permutations |
| `max_na` | float | 99 | Max % NA values per window |
| `max_zero` | float | 99 | Max % zero values per window |

**Returns:** `StereoGeneResult`

```python
@dataclass
class StereoGeneResult:
    pairs: list[PairResult]  # One per track pair
    workdir: Path            # Working directory
    log_file: Path           # StereoGene log file
    warnings: bool           # True if log contains warnings

@dataclass
class PairResult:
    track1: str              # First track name (stem)
    track2: str              # Second track name (stem)
    fg_corr: float           # Foreground (kernel) correlation
    bg_corr: float           # Background correlation
    p_value: float           # Mann-Whitney p-value
    n_fg: int                # Number of foreground windows
    fg_corr_sd: float        # Foreground correlation std dev
    bg_corr_sd: float        # Background correlation std dev
    mann_z: float            # Mann-Whitney Z score
    n_bg: int                # Number of background values
    files: dict[str, Path]   # Output files by extension
```

**Example:**

```python
result = psg.stereoGene(
    ["H3K4me3.bed", "H3K27me3.bed", "CTCF.bed"],
    chrom="hg38.chrom",
    kernel_sigma=2000,
    auto_corr=True,
    out_lc="BASE",
)

# With 3 tracks, get 3 pairs: (0,1), (0,2), (1,2)
for pair in result.pairs:
    print(f"{pair.track1} vs {pair.track2}: KC={pair.fg_corr:.3f}")
    
    # Output files available
    print(f"  Files: {list(pair.files.keys())}")
    # e.g., ['fg', 'bkg', 'dist', 'bgraph', 'LChist', 'auto']
```

---

### `pystereogene.smooth`

Track smoothing using kernel convolution.

#### `smooth(tracks, chrom, **kwargs) → SmoothResult`

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `tracks` | list[Path] | required | Input track files |
| `chrom` | Path or str | required | Chromosome lengths file |
| `kernel_sigma` | int | 1000 | Smoothing kernel width |
| `smooth_z` | float | None | Z-score threshold for output |

**Returns:** `SmoothResult`

```python
@dataclass
class SmoothResult:
    output_files: list[Path]  # *_sm.bgr files
    workdir: Path
    log_file: Path
    warnings: bool
```

**Example:**

```python
result = psg.smooth(
    ["noisy_signal.bed"],
    chrom="hg38.chrom",
    kernel_sigma=5000,
)
print(f"Smoothed file: {result.output_files[0]}")
```

---

### `pystereogene.bin_track`

Track binning into fixed-width bins.

#### `bin_track(tracks, chrom, **kwargs) → BinResult`

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `tracks` | list[Path] | required | Input track files |
| `chrom` | Path or str | required | Chromosome lengths file |
| `bin` | int | 100 | Bin size in bp |

**Returns:** `BinResult`

```python
@dataclass
class BinResult:
    output_files: list[Path]  # *_<binsize>.bgr files
    bin_size: int
    workdir: Path
    log_file: Path
    warnings: bool
```

**Example:**

```python
result = psg.bin_track(
    ["signal.bed"],
    chrom="hg38.chrom",
    bin=200,
)
# Output: signal_200.bgr
```

---

### `pystereogene.confounder`

Compute a confounder track (first principal component) for partial correlation.

#### `confounder(tracks, chrom, **kwargs) → ConfounderResult`

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `tracks` | list[Path] | required | Input tracks to compute confounder from |
| `chrom` | Path or str | required | Chromosome lengths file |

**Returns:** `ConfounderResult`

```python
@dataclass
class ConfounderResult:
    bgraph_file: Path    # confounder.bgraph
    covar_file: Path     # confounder.covar (covariance matrix)
    bprof_file: Path     # Binary profile (if exists)
    workdir: Path
    log_file: Path
    warnings: bool
```

**Example:**

```python
# Compute confounder from multiple histone marks
conf = psg.confounder(
    ["H3K4me3.bed", "H3K27me3.bed", "H3K36me3.bed"],
    chrom="hg38.chrom",
)

# Parse the covariance matrix
from pystereogene.parsing import parse_covar
matrix, eigenvector, eigenvalue = parse_covar(conf.covar_file)
```

---

### `pystereogene.project`

Project tracks to remove confounder effect (for partial correlation).

#### `project(tracks, chrom, confounder_track, **kwargs) → ProjectResult`

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `tracks` | list[Path] | required | Tracks to project |
| `chrom` | Path or str | required | Chromosome lengths file |
| `confounder_track` | Path | required | Confounder bedGraph (from `confounder()`) |

**Returns:** `ProjectResult`

```python
@dataclass
class ProjectResult:
    projected_files: list[Path]  # Projected .bgraph files
    config_file: Path            # Generated config
    projections_log: Path        # Projection coefficients
    workdir: Path
    log_file: Path
    warnings: bool
```

**Example:**

```python
# Full partial correlation workflow
conf = psg.confounder(histone_marks, "hg38.chrom")

proj = psg.project(
    ["track1.bed", "track2.bed"],
    "hg38.chrom",
    confounder_track=conf.bgraph_file,
)

# Correlate with confounder effect removed
result = psg.stereoGene(proj.projected_files, "hg38.chrom")
```

---

### `pystereogene.parse_genes`

Parse GTF/GFF or BED12 gene annotations into feature BED files.

#### `parse_genes(annotation, **kwargs) → ParseGenesResult`

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `annotation` | Path | required | GTF (GENCODE) or BED12 (RefSeq) file |
| `track_dir` | Path | None | Output directory (temp if None) |
| `gencode_level` | int | 2 | GENCODE confidence level (1, 2, or 3) |
| `biotypes` | str or list | None | Gene biotypes to include |

**Returns:** `ParseGenesResult`

```python
@dataclass
class ParseGenesResult:
    gene: Path       # *_gene.bed - gene bodies
    gene_beg: Path   # *_g_beg.bed - gene starts (TSS)
    gene_end: Path   # *_g_end.bed - gene ends (TTS)
    exon: Path       # *_exn.bed - exon bodies
    exon_beg: Path   # *_e_beg.bed - exon starts
    exon_end: Path   # *_e_end.bed - exon ends
    intron: Path     # *_ivs.bed - intron bodies
    intron_beg: Path # *_i_beg.bed - intron starts
    intron_end: Path # *_i_end.bed - intron ends
    workdir: Path
```

**Example:**

```python
result = psg.parse_genes(
    "gencode.v38.annotation.gtf",
    gencode_level=2,
    biotypes=["protein_coding", "lncRNA"],
)

# Correlate histone marks with TSS
corr = psg.stereoGene(
    [result.gene_beg, "H3K4me3.bed"],
    "hg38.chrom",
)
```

---

### `pystereogene.model`

Builder for StereoGene model files (.mod) that combine tracks with formulas.

#### `ModelFile`

```python
class ModelFile:
    def add_track(self, name: str, path: Path, shift: int = 0) -> ModelFile
    def set_formula(self, expr: str) -> ModelFile
    def add_line(self, line: str) -> ModelFile
    def write(self, path: Path) -> Path
```

**Supported formula syntax:**
- Track references: `[filename.wig]` or `[filename.wig](x+1000)` (with shift)
- Arithmetic: `+ - * /`
- Functions: `log exp sin cos tan sqrt abs sign atan`
- Variables: `x` (position), `e` (kernelShift), `sigma` (kernelSigma)

**Example:**

```python
from pystereogene import ModelFile

model = ModelFile()
model.add_track("K27", "/abs/path/H3K27me3.wig")
model.add_track("K4", "/abs/path/H3K4me3.wig", shift=1000)
model.set_formula("log(K27 + 1) * K4")
model.write("combined.mod")

result = psg.stereoGene(["combined.mod", "CTCF.bed"], "hg38.chrom")
```

**Note:** Use absolute paths in model files.

---

### `pystereogene.parsing`

Output file parsers. Functions returning DataFrames require pandas.

```python
from pystereogene import parsing

# NumPy arrays (no pandas required)
fg = parsing.parse_fg(path)           # .fg → np.ndarray
bkg = parsing.parse_bkg(path)         # .bkg → np.ndarray

# DataFrames (require pandas)
dist = parsing.parse_dist(path)       # .dist → DataFrame
bgraph = parsing.parse_bgraph(path)   # .bgraph → DataFrame
auto = parsing.parse_auto(path)       # .auto → DataFrame
spect = parsing.parse_spect(path)     # .spect → DataFrame
lchist = parsing.parse_lchist(path)   # .LChist → DataFrame
stats = parsing.parse_statistics(path)  # statistics.tsv → DataFrame
params = parsing.parse_params(path)     # params.tsv → DataFrame

# Special formats
matrix, eigvec, eigval = parsing.parse_covar(path)  # .covar → (ndarray, ndarray, float)
proj_df = parsing.parse_projections_log(path)       # projections → DataFrame
```

---

### `pystereogene.chrom`

Chromosome file resolution.

```python
from pystereogene import resolve_chrom

# Bundled genomes
path = resolve_chrom("hg19")  # Returns path to bundled hg19_chrom

# Custom file
path = resolve_chrom("/path/to/hg38.chrom.sizes")

# List available shortcuts
from pystereogene.chrom import list_bundled
print(list_bundled())  # ['hg18', 'hg19']
```

**Bundled:** `hg18`, `hg19`

**hg38:** Download from UCSC:
```bash
wget https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chrom.sizes
```

---

### `pystereogene.params`

Parameter enums for type-safe configuration.

```python
from pystereogene.params import (
    KernelType,   # NORMAL, LEFT_EXP, RIGHT_EXP
    BpType,       # SCORE, SIGNAL, LOGPVAL
    WriteDistr,   # NONE, SHORT, DETAIL
    OutLC,        # OFF, BASE, CENTER
    PlotType,     # NONE, R, PDF, HTML, ALL
)

result = psg.stereoGene(
    tracks, chrom,
    kernel_type=KernelType.NORMAL,
    write_distr=WriteDistr.DETAIL,
    out_lc=OutLC.BASE,
)
```

---

### `pystereogene.exceptions`

```python
from pystereogene import StereoGeneError

try:
    result = psg.stereoGene(tracks, chrom)
except StereoGeneError as e:
    print(f"StereoGene failed: {e}")
```

---

## Advanced Usage

### Profile Caching

Cache binary profiles across runs for faster recomputation:

```python
result = psg.stereoGene(
    tracks, chrom,
    cache_dir="~/.stereogene_cache",
)
```

Profiles are reused when input file path, mtime, and `bin` size are unchanged.

### Parallel Execution

**Important:** Use `ProcessPoolExecutor`, not `ThreadPoolExecutor`. StereoGene uses global state internally.

```python
from concurrent.futures import ProcessPoolExecutor

def analyze_pair(tracks):
    return psg.stereoGene(tracks, "hg38.chrom")

pairs = [["a.bed", "b.bed"], ["c.bed", "d.bed"], ...]

with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(analyze_pair, pairs))
```

### Keeping Output Files

By default, the working directory is deleted after the result is returned. To keep files:

```python
result = psg.stereoGene(
    tracks, chrom,
    workdir="/path/to/output",  # Use a specific directory
    keep_workdir=True,          # Don't delete it
)

# All output files are in result.workdir
print(result.workdir)
```

---

## File Format Notes

### Input Tracks

StereoGene detects format by file extension:
- `.bed` — BED (score column used as signal)
- `.wig`, `.wiggle` — WIG
- `.bgr`, `.bgraph`, `.bedgraph` — bedGraph
- `.broadpeak`, `.bpeak` — BroadPeak (use `bp_type` to select column)
- `.narrowpeak`, `.npeak` — NarrowPeak
- `.mod`, `.model` — Model file

### Chromosome File

Tab-separated: `chrom_name<TAB>length`

```
chr1	248956422
chr2	242193529
...
```

Chromosome names must exactly match the track files.

---

## Building from Source

If binaries aren't built during install:

```python
from pystereogene.build import build
build()  # Compiles and installs binaries
```

Or from command line:

```bash
python -m pystereogene.build
```

---

## Citation

If you use pystereogene, please cite:

> Stavrovskaya ED, Nirber T, Cremona MA, et al. (2017) StereoGene: Rapid Estimation of Genome-Wide Correlation of Continuous or Interval Feature Data. *Bioinformatics* 33(20):3158-3165. doi:10.1093/bioinformatics/btx379

---

## License

MIT License
