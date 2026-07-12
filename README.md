# pystereogene

Python wrapper for [StereoGene](https://github.com/favorov/stereogene) (v2.51) — genome-wide correlation analysis of continuous or interval genomic features using kernel convolution and FFT.

## Installation

```bash
git clone https://github.com/dkhlebn/pystereogene.git
cd pystereogene
pip install -e .

# With pandas/matplotlib support
pip install -e ".[full]"
```

**Requirements:** Linux or macOS, Python 3.9+, gcc/g++ (binaries compile at install time).

## Quick Start

```python
import pystereogene as psg

result = psg.stereoGene(
    ["H3K4me3.bed", "H3K27me3.bed"],
    chrom="hg38.chrom",
)

for pair in result.pairs:
    print(f"{pair.track1} vs {pair.track2}: KC={pair.fg_corr:.3f}, p={pair.p_value:.2e}")
```

## Functions

| Function | Description |
|----------|-------------|
| `stereoGene()` | Compute kernel correlation between tracks |
| `smooth()` | Smooth tracks using kernel convolution |
| `bin_track()` | Bin tracks into fixed-width bins |
| `confounder()` | Compute confounder track (1st principal component) |
| `project()` | Remove confounder effect from tracks |
| `parse_genes()` | Parse GTF/BED12 into gene feature BED files |

## Working Directory and Intermediate Files

By default, all functions create a temporary directory for intermediate files which is **deleted after the function returns**. 

To keep the files:

```python
# Option 1: Provide your own directory (never auto-deleted)
result = psg.stereoGene(tracks, chrom, workdir="/path/to/output")

# Option 2: Use temp dir but keep it
result = psg.stereoGene(tracks, chrom, keep_workdir=True)
print(result.workdir)  # Temp path preserved
```

**Note:** If `keep_workdir=False` (default) and no `workdir` is provided, the `files` dict and `workdir` path in results will point to deleted locations. Use `keep_workdir=True` or provide a `workdir` if you need to access output files.

## Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workdir` | Path | None | Output directory (temp if None) |
| `keep_workdir` | bool | False | Keep working directory after completion |
| `cache_dir` | Path | None | Persistent profile cache directory |
| `bin` | int | 100 | Bin size in bp |
| `kernel_sigma` | int | 1000 | Kernel width in bp |
| `w_size` | int | 100000 | Window size in bp |
| `auto_corr` | bool | False | Compute autocorrelation |
| `cross` | bool | True | Compute cross-correlation |
| `out_lc` | str | "0" | Local correlation: "0", "BASE", "CENTER" |

## Examples

### Basic Correlation

```python
import pystereogene as psg

result = psg.stereoGene(
    ["track1.bed", "track2.bed", "track3.bed"],
    chrom="hg38.chrom",
    kernel_sigma=2000,
    keep_workdir=True,
)

for pair in result.pairs:
    print(f"{pair.track1} vs {pair.track2}")
    print(f"  KC: {pair.fg_corr:.4f} ± {pair.fg_corr_sd:.4f}")
    print(f"  p-value: {pair.p_value:.2e}")
    
    # Parse output files
    if "fg" in pair.files:
        from pystereogene.parsing import parse_fg
        fg = parse_fg(pair.files["fg"])
```

### Partial Correlation

```python
# Compute confounder
conf = psg.confounder(
    ["H3K4me3.bed", "H3K27me3.bed", "H3K36me3.bed"],
    chrom="hg38.chrom",
    keep_workdir=True,
)

# Project tracks
proj = psg.project(
    ["track1.bed", "track2.bed"],
    chrom="hg38.chrom",
    confounder_track=conf.bgraph_file,
    keep_workdir=True,
)

# Correlate projected tracks
result = psg.stereoGene(proj.projected_files, "hg38.chrom")
```

### Gene Annotation

```python
genes = psg.parse_genes(
    "gencode.gtf",
    gencode_level=2,
    biotypes=["protein_coding"],
    keep_workdir=True,
)

# Correlate with TSS
result = psg.stereoGene([genes.gene_beg, "H3K4me3.bed"], "hg38.chrom")
```

### Model Files

```python
from pystereogene import ModelFile

model = ModelFile()
model.add_track("K27", "/path/to/H3K27me3.wig")
model.add_track("K4", "/path/to/H3K4me3.wig", shift=1000)
model.set_formula("K27 * K4")
model.write("combined.mod")

result = psg.stereoGene(["combined.mod", "CTCF.bed"], "hg38.chrom")
```

## Output Parsing

```python
from pystereogene.parsing import (
    parse_fg,        # .fg - numpy array
    parse_bkg,       # .bkg - numpy array  
    parse_dist,      # .dist - DataFrame (requires pandas)
    parse_bgraph,    # .bgraph - DataFrame
    parse_covar,     # .covar - (matrix, eigenvector, eigenvalue)
)
```

## Chromosome Files

Bundled: `hg18`, `hg19`

```python
psg.stereoGene(tracks, chrom="hg19")  # Uses bundled file
```

For hg38:
```bash
wget https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chrom.sizes
```

## Parallel Execution

Use `ProcessPoolExecutor` (not threads):

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(
        lambda t: psg.stereoGene(t, "hg38.chrom"),
        track_pairs
    ))
```

## Package Structure

```
pystereogene/
├── __init__.py        # Public API
├── correlate.py       # stereoGene()
├── smooth.py          # smooth()
├── bin_track.py       # bin_track()
├── confounder.py      # confounder()
├── project.py         # project()
├── parse_genes.py     # parse_genes()
├── parsing.py         # Output file parsers
├── model.py           # ModelFile builder
├── chrom.py           # Chromosome file resolution
├── params.py          # Parameter enums
├── exceptions.py      # StereoGeneError
├── build.py           # Build script
├── _bin.py            # Binary resolver
├── _runner.py         # Subprocess infrastructure
├── _vendor/
│   ├── bin/           # Compiled binaries
│   └── src/           # C++ source
└── tests/
    └── data/          # Test data
```

## Building Binaries

Binaries compile automatically during install. To rebuild:

```bash
python -m pystereogene.build
```

## Citation

> Stavrovskaya ED, et al. (2017) StereoGene: Rapid Estimation of Genome-Wide Correlation of Continuous or Interval Feature Data. *Bioinformatics* 33(20):3158-3165.
