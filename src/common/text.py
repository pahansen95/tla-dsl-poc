#!/usr/bin/env python3
"""
Text Extraction Module

Unified text extraction utilities for both CST and AST nodes.
Consolidates duplicate text extraction logic across packages.
"""

from typing import Union, List
from .inspection import is_cst_token, is_cst_tree


def extract_raw_text(node) -> str:
  """
  Extract all text content from any node type.

  Recursively traverses tree structures to collect all text.

  Args:
      node: Any node type (CST Tree, Token, or other)

  Returns:
      Concatenated text content
  """
  if is_cst_token(node):
    return str(node)
  elif is_cst_tree(node):
    return "".join(extract_raw_text(child) for child in node.children)
  elif hasattr(node, "__str__"):
    return str(node)
  return ""


def extract_text(node, mode: str = "line") -> Union[str, List[str]]:
  """
  Extract text content in various formats.

  Modes:
    - 'raw': Unprocessed text including whitespace
    - 'line': Single line with normalized whitespace
    - 'lines': List of normalized lines

  Args:
      node: Node to extract text from
      mode: Extraction mode

  Returns:
      Text as string or list of strings based on mode
  """
  raw = extract_raw_text(node)

  if mode == "raw":
    return raw
  elif mode == "line":
    return normalize_line(raw)
  elif mode == "lines":
    return split_into_lines(raw)
  else:
    raise ValueError(f"Unknown extraction mode: {mode}")


def normalize_line(text: str) -> str:
  """Normalize whitespace in text to single line."""
  return " ".join(text.split())


def split_into_lines(text: str) -> List[str]:
  """Split text into normalized lines, removing empty lines."""
  lines = []
  for line in text.split("\n"):
    normalized = normalize_line(line)
    if normalized:
      lines.append(normalized)
  return lines
