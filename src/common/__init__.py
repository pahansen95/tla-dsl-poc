#!/usr/bin/env python3
"""
Common Utilities Package

Cross-cutting utilities shared across CST, AST, and serialization domains.
"""

from .metadata import extract_position, apply_position
from .inspection import is_cst_tree, is_cst_token, is_ast_node, is_serializable_node, get_node_type
from .text import extract_text, extract_raw_text, normalize_line, split_into_lines
from .tokens import TokenFactory

__all__ = [
  # Metadata utilities
  "extract_position",
  "apply_position",
  # Inspection utilities
  "is_cst_tree",
  "is_cst_token",
  "is_ast_node",
  "is_serializable_node",
  "get_node_type",
  # Text utilities
  "extract_text",
  "extract_raw_text",
  "normalize_line",
  "split_into_lines",
  # Token utilities
  "TokenFactory",
]
