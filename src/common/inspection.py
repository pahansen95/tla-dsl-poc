#!/usr/bin/env python3
"""
Node Inspection Module

Centralized type checking and node inspection utilities.
Reduces isinstance() calls scattered throughout the codebase.
"""

from typing import Any


def is_cst_tree(node: Any) -> bool:
  """Check if node is a CST Tree."""
  try:
    from lark import Tree

    return isinstance(node, Tree)
  except ImportError:
    return False


def is_cst_token(node: Any) -> bool:
  """Check if node is a CST Token."""
  try:
    from lark import Token

    return isinstance(node, Token)
  except ImportError:
    return False


def is_ast_node(node: Any) -> bool:
  """
  Check if node is an AST node.

  AST nodes are identified by having both __dict__ and accept() method.
  """
  return hasattr(node, "__dict__") and hasattr(node, "accept") and callable(getattr(node, "accept", None))


def is_serializable_node(node: Any) -> bool:
  """Check if node can be serialized (CST or AST node)."""
  return is_cst_tree(node) or is_cst_token(node) or is_ast_node(node)


def get_node_type(node: Any) -> str:
  """
  Get descriptive type name for a node.

  Returns:
      'tree', 'token', 'ast', or 'unknown'
  """
  if is_cst_tree(node):
    return "tree"
  elif is_cst_token(node):
    return "token"
  elif is_ast_node(node):
    return "ast"
  else:
    return "unknown"
