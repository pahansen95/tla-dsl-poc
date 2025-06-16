#!/usr/bin/env python3
"""
AST Utilities

Helper functions for AST operations including text extraction.
"""

from typing import Union, List
from lark import Tree, Token


def extract_text(node, mode: str = "line") -> Union[str, List[str]]:
  """
  Extract text content from CST nodes in various formats.

  Args:
      node: CST node to extract from
      mode: Extraction mode
          - 'raw': Unprocessed text including whitespace
          - 'line': Single line with normalized whitespace
          - 'lines': List of normalized lines

  Returns:
      Extracted text as string or list of strings
  """
  raw = _get_raw_text(node)

  if mode == "raw":
    return raw
  elif mode == "line":
    return " ".join(raw.split())
  elif mode == "lines":
    return _split_into_lines(raw)
  else:
    raise ValueError(f"Unknown extraction mode: {mode}")


def _get_raw_text(node) -> str:
  """Recursively extract all text content."""
  if isinstance(node, Token):
    return str(node)
  elif isinstance(node, Tree):
    return "".join(_get_raw_text(child) for child in node.children)
  return str(node)


def _split_into_lines(raw: str) -> List[str]:
  """Split text into normalized lines."""
  lines = []
  for line in raw.split("\n"):
    normalized = " ".join(line.split())
    if normalized:
      lines.append(normalized)
  return lines


def create_indent(level: int, size: int = 2) -> Token:
  """
  Create indentation token.

  Args:
      level: Indentation level (1 or 2)
      size: Spaces per indent level

  Returns:
      Indent token with appropriate type
  """
  spaces = " " * (size * level)
  token_type = "INDENT" if level == 1 else "DOUBLE_INDENT"
  return Token(token_type, spaces)
