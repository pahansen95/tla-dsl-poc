"""Type definitions for Natural Specification Language.

Provides type aliases and TypedDict definitions for structured data
throughout the NSL package.
"""

# Standard library imports
from typing import TypedDict


class FormatStyle(TypedDict, total=False):
  """Formatting style configuration for NSL text generation."""

  indent_size: int  # Number of spaces per indent level
  bullet_char: str  # Character for bullet points (e.g., '-', '*')
  section_spacing: int  # Blank lines between sections


# Explicit exports
__all__ = [
  "FormatStyle",
]
