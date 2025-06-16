#!/usr/bin/env python3
"""
Metadata Extraction Module

Provides utilities for extracting position and other metadata
from CST nodes. Eliminates duplication across packages.
"""

from typing import Dict, Any


def extract_position(node) -> Dict[str, Any]:
  """
  Extract position metadata from any node type.

  Handles both direct position attributes and nested meta objects.

  Args:
      node: CST Tree or Token with position information

  Returns:
      Dictionary containing available position fields
  """
  source = getattr(node, "meta", node) if hasattr(node, "meta") else node

  position_fields = ["line", "column", "end_line", "end_column"]

  return {
    attr: getattr(source, attr)
    for attr in position_fields
    if hasattr(source, attr) and getattr(source, attr) is not None
  }


def apply_position(node, position: Dict[str, Any]) -> None:
  """
  Apply position metadata to a node.

  Creates a meta object if needed for Tree nodes.

  Args:
      node: CST node to update
      position: Position dictionary to apply
  """
  if not position:
    return

  # For Tree nodes, create meta object
  if hasattr(node, "meta"):
    if not hasattr(node, "meta") or node.meta is None:
      node.meta = type("Meta", (), {})()

    for key, value in position.items():
      setattr(node.meta, key, value)
  else:
    # For Token nodes, set attributes directly
    for key, value in position.items():
      if hasattr(node, key):
        setattr(node, key, value)
