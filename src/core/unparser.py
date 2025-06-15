#!/usr/bin/env python3
"""
CST Unparsing Module

This module reconstructs the original text representation from a Concrete
Syntax Tree (CST). It provides the inverse operation of parsing, transforming
structured tree data back into human-readable DSL documents.

Responsibilities:
- Convert CST nodes back to their text representation
- Preserve exact formatting including whitespace and indentation
- Support both Tree and Token node types from Lark
- Enable perfect roundtrip parsing (parse → unparse → identical text)

The unparsing process is deterministic and preserves all textual information
captured during parsing, making it suitable for document transformation
pipelines and validation workflows.
"""

from lark import Tree, Token
from typing import Union


def unparse_tree(node: Union[Tree, Token]) -> str:
  """
  Convert a CST node back to its text representation.

  This function recursively traverses the CST and reconstructs the
  original text by concatenating all token values in order.

  Args:
      node: A Lark Tree or Token object from the CST

  Returns:
      The text representation of the node and all its children

  Note:
      This assumes the parser was configured with keep_all_tokens=True
      to preserve whitespace and formatting tokens.
  """
  if isinstance(node, Token):
    # Tokens contain the actual text values
    return str(node)

  elif isinstance(node, Tree):
    # Trees are internal nodes - reconstruct by concatenating children
    return "".join(unparse_tree(child) for child in node.children)

  else:
    # Handle literal values (strings, etc) that might appear in the tree
    return str(node)


def unparse_subtree(tree: Tree, rule_name: str) -> str:
  """
  Unparse a specific subtree by rule name.

  Finds the first subtree matching the given rule name and unparses it.
  Useful for extracting specific sections of a document.

  Args:
      tree: The root CST to search
      rule_name: The grammar rule name to find

  Returns:
      Text representation of the first matching subtree,
      or empty string if not found
  """
  for subtree in tree.find_data(rule_name):
    return unparse_tree(subtree)
  return ""


def extract_tokens(node: Union[Tree, Token]) -> list[str]:
  """
  Extract all token values from a CST node.

  Collects all terminal token values in order, useful for analysis
  or transformation operations.

  Args:
      node: CST node to extract tokens from

  Returns:
      List of token string values in document order
  """
  tokens = []

  if isinstance(node, Token):
    tokens.append(str(node))
  elif isinstance(node, Tree):
    for child in node.children:
      tokens.extend(extract_tokens(child))

  return tokens


def unparse_without_whitespace(node: Union[Tree, Token]) -> str:
  """
  Unparse a CST node while filtering out pure whitespace tokens.

  Useful for comparing document structure without formatting differences.

  Args:
      node: CST node to unparse

  Returns:
      Text with whitespace tokens removed (but preserving space
      within other tokens)
  """
  if isinstance(node, Token):
    # Check if this is a whitespace-only token
    if node.type in ("WS", "NEWLINE", "INDENT", "DOUBLE_INDENT"):
      return ""
    return str(node)

  elif isinstance(node, Tree):
    return "".join(unparse_without_whitespace(child) for child in node.children)

  return str(node)
