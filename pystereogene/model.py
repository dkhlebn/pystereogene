"""Model file builder for StereoGene track combination."""

from __future__ import annotations

from pathlib import Path


class ModelFile:
    """
    Builder for StereoGene .mod model files.

    Model files combine multiple tracks via arithmetic formulas. The formula
    language supports:
    - Track references: [filename.wig] or [filename.wig](x+1000) with shift
    - Arithmetic: + - * /
    - Math functions: log exp sin cos tan sqrt abs sign atan
    - Variables: x = genome position, e = kernelShift, sigma = kernelSigma

    Example:
        >>> m = ModelFile()
        >>> m.add_track("K27", "H3K27me3.wig")
        >>> m.add_track("K4", "H3K4me3.wig", shift=1000)
        >>> m.set_formula("K27 * K4")
        >>> m.write("combined.mod")

    Note:
        Track paths inside the model file should be absolute paths, since
        StereoGene resolves them relative to trackPath which may be a temp dir.
    """

    def __init__(self) -> None:
        self._lines: list[str] = []

    def add_track(self, name: str, path: str | Path, shift: int = 0) -> "ModelFile":
        """
        Add a track reference with an optional position shift.

        Args:
            name: Variable name for this track in the formula.
            path: Path to the track file. Use absolute paths.
            shift: Shift the track by this many base pairs (default 0).

        Returns:
            self for method chaining.
        """
        path = Path(path).resolve() if not Path(path).is_absolute() else Path(path)
        ref = f"[{path}]"
        if shift:
            ref += f"(x+{shift})"
        self._lines.append(f"{name} = {ref};")
        return self

    def set_formula(self, expr: str) -> "ModelFile":
        """
        Set the output formula combining the tracks.

        Args:
            expr: Formula expression using track variable names and arithmetic.

        Returns:
            self for method chaining.
        """
        self._lines.append(expr)
        return self

    def add_line(self, line: str) -> "ModelFile":
        """
        Add a raw line to the model file.

        Args:
            line: Raw line to add (variable assignment or expression).

        Returns:
            self for method chaining.
        """
        self._lines.append(line)
        return self

    def write(self, path: str | Path) -> Path:
        """
        Write the model file to disk.

        Args:
            path: Output path for the .mod file.

        Returns:
            Path to the written file.
        """
        path = Path(path)
        path.write_text("\n".join(self._lines) + "\n")
        return path

    def __str__(self) -> str:
        return "\n".join(self._lines)
