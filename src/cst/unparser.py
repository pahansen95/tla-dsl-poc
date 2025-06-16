#!/usr/bin/env python3
"""
CST Unparser Module

Reconstructs text from Concrete Syntax Trees.
"""

from lark import Tree, Token
from typing import Union


def unparse_tree(node: Union[Tree, Token]) -> str:
  """
  Convert a CST node back to its text representation.

  Recursively traverses the CST and concatenates all token values
  to reconstruct the original document text.

  Args:
      node: Lark Tree or Token from the CST

  Returns:
      Text representation of the node and all children

  Note:
      Requires parser configured with keep_all_tokens=True
  """
  if isinstance(node, Token):
    return str(node)
  elif isinstance(node, Tree):
    return "".join(unparse_tree(child) for child in node.children)
  else:
    return str(node)
