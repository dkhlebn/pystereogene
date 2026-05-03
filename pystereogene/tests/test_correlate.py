"""Tests for the stereoGene correlation function."""

import pytest
from pathlib import Path

from pystereogene import stereoGene, StereoGeneError
from pystereogene._bin import binaries_available


@pytest.mark.skipif(not binaries_available(), reason="Binaries not built")
def test_stereogene_basic(track_files, chrom_file, tmp_path):
    """Test basic stereoGene functionality."""
    result = stereoGene(
        track_files,
        chrom_file,
        workdir=tmp_path,
        keep_workdir=True,
    )

    assert len(result.pairs) == 1
    pair = result.pairs[0]

    assert pair.track1 == "H3K4me1"
    assert pair.track2 == "H3K4me3"
    assert isinstance(pair.fg_corr, float)
    assert isinstance(pair.p_value, float)
    assert pair.p_value >= 0
    assert pair.n_fg > 0

    assert result.workdir == tmp_path
    assert result.log_file.exists()


@pytest.mark.skipif(not binaries_available(), reason="Binaries not built")
def test_stereogene_output_files(track_files, chrom_file, tmp_path):
    """Test that output files are created."""
    result = stereoGene(
        track_files,
        chrom_file,
        workdir=tmp_path,
        keep_workdir=True,
        cross=True,
    )

    pair = result.pairs[0]

    assert "fg" in pair.files
    assert pair.files["fg"].exists()

    assert "bkg" in pair.files
    assert pair.files["bkg"].exists()

    assert "dist" in pair.files
    assert pair.files["dist"].exists()


@pytest.mark.skipif(not binaries_available(), reason="Binaries not built")
def test_stereogene_autocorr(track_files, chrom_file, tmp_path):
    """Test autocorrelation output."""
    result = stereoGene(
        track_files,
        chrom_file,
        workdir=tmp_path,
        keep_workdir=True,
        auto_corr=True,
    )

    pair = result.pairs[0]
    assert "auto" in pair.files
    assert pair.files["auto"].exists()


def test_stereogene_missing_track(chrom_file, tmp_path):
    """Test error handling for missing track file."""
    with pytest.raises(FileNotFoundError):
        stereoGene(
            ["/nonexistent/track.bed"],
            chrom_file,
            workdir=tmp_path,
        )


def test_stereogene_missing_chrom(track_files, tmp_path):
    """Test error handling for missing chromosome file."""
    with pytest.raises(FileNotFoundError):
        stereoGene(
            track_files,
            "/nonexistent/chrom.sizes",
            workdir=tmp_path,
        )
