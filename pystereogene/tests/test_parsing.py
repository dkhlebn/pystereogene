"""Tests for the parsing module."""

import pytest
import numpy as np
from pathlib import Path
from io import StringIO

from pystereogene import parsing


def test_parse_fg_short(tmp_path):
    """Test parsing SHORT format .fg file."""
    fg_file = tmp_path / "test.fg"
    fg_file.write_text("0.123\n0.456\n0.789\n")

    result = parsing.parse_fg(fg_file)

    assert isinstance(result, np.ndarray)
    assert len(result) == 3
    assert np.allclose(result, [0.123, 0.456, 0.789])


def test_parse_bkg(tmp_path):
    """Test parsing .bkg file."""
    bkg_file = tmp_path / "test.bkg"
    bkg_file.write_text("-0.01\n0.02\n-0.03\n")

    result = parsing.parse_bkg(bkg_file)

    assert isinstance(result, np.ndarray)
    assert len(result) == 3


def test_parse_covar(tmp_path):
    """Test parsing .covar file."""
    covar_content = """\t track1\ttrack2\ttrack3
track1\t1.0000\t0.4231\t-0.1023
track2\t0.4231\t1.0000\t0.2017
track3\t-0.1023\t0.2017\t1.0000
eigenVector =\t0.612\t0.541\t0.577

eigenValue=1.87432;
"""
    covar_file = tmp_path / "test.covar"
    covar_file.write_text(covar_content)

    matrix, eigenvector, eigenvalue = parsing.parse_covar(covar_file)

    assert matrix.shape == (3, 3)
    assert np.isclose(matrix[0, 0], 1.0)
    assert np.isclose(matrix[0, 1], 0.4231)

    assert len(eigenvector) == 3
    assert np.isclose(eigenvector[0], 0.612)

    assert np.isclose(eigenvalue, 1.87432)
