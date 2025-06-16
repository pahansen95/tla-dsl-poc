#!/usr/bin/env python3
"""
AST Utilities

Helper functions specific to AST operations.
"""

from common import extract_text as common_extract_text, TokenFactory


def extract_text(node, mode: str = "line"):
  """
  Extract text from CST nodes.

  Delegates to common text extraction for consistency.

  Args:
      node: CST node to extract from
      mode: 'raw', 'line', or 'lines'

  Returns:
      Extracted text based on mode
  """
  return common_extract_text(node, mode)


def create_indent(level: int, size: int = 2):
  """
  Create indentation token.

  Delegates to common TokenFactory for consistent token creation.

  Args:
      level: Indentation level (1 or 2)
      size: Spaces per indent level

  Returns:
      INDENT or DOUBLE_INDENT token
  """
  return TokenFactory.indent(level, size)
