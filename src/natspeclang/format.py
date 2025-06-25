"""Format detection and specification parsing.

Handles automatic format detection from filenames and parsing of format
specifications with encoding options.
"""

# Standard library imports
from pathlib import Path
from typing import Dict, Final, Optional

# Local imports
from .pipeline import Format


# Module constants
DEFAULT_OUTPUT_FORMATS: Final[Dict[str, str]] = {
  Format.NSL: Format.AST_TEXT,
  Format.CST: Format.AST,
  Format.CST_JSON: Format.AST,
  Format.AST: Format.AST_TEXT,
  Format.AST_JSON: Format.AST_TEXT,
  Format.AST_TEXT: Format.NSL,
}


class FormatDetector:
  """Detects and parses format specifications.

  Provides format detection from filenames and parsing of format
  specification strings with support for various encoding options.
  """

  __slots__ = ()

  # Extension to format mapping
  EXTENSIONS: Final[Dict[str, str]] = {
    ".nsl": Format.NSL,
    ".dsl": Format.NSL,
    ".cst": Format.CST_JSON,
    ".cst.json": Format.CST_JSON,
    ".ast": Format.AST_TEXT,
    ".ast.json": Format.AST_JSON,
    ".ast.txt": Format.AST_TEXT,
    # Future extensions
    # '.ir': Format.IR,
    # '.ir.json': Format.IR_JSON,
    # '.tla': Format.TLA,
  }

  # Format string mapping
  FORMAT_STRINGS: Final[Dict[str, str]] = {
    "nsl": Format.NSL,
    "dsl": Format.NSL,
    "cst": Format.CST,
    "cst.json": Format.CST_JSON,
    "cst:json": Format.CST_JSON,
    "ast": Format.AST,
    "ast.json": Format.AST_JSON,
    "ast:json": Format.AST_JSON,
    "ast.text": Format.AST_TEXT,
    "ast:text": Format.AST_TEXT,
  }

  # Default file extensions for formats
  DEFAULT_EXTENSIONS: Final[Dict[str, str]] = {
    Format.NSL: ".nsl",
    Format.CST: ".cst",
    Format.CST_JSON: ".cst.json",
    Format.AST: ".ast",
    Format.AST_JSON: ".ast.json",
    Format.AST_TEXT: ".ast.txt",
  }

  @classmethod
  def from_filename(cls, filename: str) -> Optional[str]:
    """Detect format from filename extension.

    Tries compound extensions first (e.g., .ast.json) then simple
    extensions. Returns None if format cannot be determined.

    Args:
        filename: Path or filename to analyze

    Returns:
        Format string constant or None if unrecognized
    """
    # Normalize path
    Path(filename)

    # Try compound extensions by checking suffix matches
    # Sort by length descending to match longest first
    for ext, fmt in sorted(cls.EXTENSIONS.items(), key=lambda x: -len(x[0])):
      if filename.endswith(ext):
        return fmt

    return None

  @classmethod
  def parse_format_spec(cls, spec: str) -> str:
    """Parse format specification string.

    Supports formats:
    - Simple: 'ast', 'cst', 'nsl'
    - With encoding: 'ast:json', 'cst:json'
    - Dotted: 'ast.json', 'cst.json'

    Args:
        spec: Format specification string

    Returns:
        Validated format string constant

    Raises:
        ValueError: If format specification is invalid
    """
    spec_lower = spec.lower()

    # Direct lookup
    if spec_lower in cls.FORMAT_STRINGS:
      return Format.validate(cls.FORMAT_STRINGS[spec_lower])

    # Handle format:encoding syntax
    if ":" in spec_lower:
      fmt, encoding = spec_lower.split(":", 1)
      combined = f"{fmt}:{encoding}"
      if combined in cls.FORMAT_STRINGS:
        return Format.validate(cls.FORMAT_STRINGS[combined])

      # Try default encodings
      if fmt == "cst" and encoding == "json":
        return Format.CST_JSON
      elif fmt == "ast" and encoding == "json":
        return Format.AST_JSON
      elif fmt == "ast" and encoding == "text":
        return Format.AST_TEXT

    raise ValueError(f"Unknown format specification: '{spec}'")

  @classmethod
  def get_default_extension(cls, format_str: str) -> str:
    """Get default file extension for a format.

    Args:
        format_str: Format string constant

    Returns:
        Default file extension including dot
    """
    # Validate format
    Format.validate(format_str)

    return cls.DEFAULT_EXTENSIONS.get(format_str, ".txt")

  @classmethod
  def get_default_output_format(cls, input_format: str) -> str:
    """Get sensible default output format for a given input.

    Args:
        input_format: Input format string constant

    Returns:
        Default output format string constant
    """
    # Validate format
    Format.validate(input_format)

    return DEFAULT_OUTPUT_FORMATS.get(input_format, Format.AST_TEXT)


# Public functions
def detect_format(filename: str) -> Optional[str]:
  """Convenience function for format detection from filename."""
  return FormatDetector.from_filename(filename)


def parse_format(spec: str) -> str:
  """Convenience function for parsing format specifications."""
  return FormatDetector.parse_format_spec(spec)


# Explicit exports
__all__ = [
  # Main class
  "FormatDetector",
  # Convenience functions
  "detect_format",
  "parse_format",
]
