#!/usr/bin/env python3
"""
CST Navigation Module

Tree traversal and navigation utilities specific to Concrete Syntax Trees.
"""

from typing import Optional, List
from lark import Tree
from common import TokenFactory


def find_child(tree: Tree, name: str) -> Optional[Tree]:
  """
  Find first child with given rule name.

  Args:
      tree: Parent tree to search
      name: Rule name to find

  Returns:
      First matching child tree or None
  """
  if not isinstance(tree, Tree):
    return None

  for child in tree.children:
    if isinstance(child, Tree) and child.data == name:
      return child
  return None


def find_all(tree: Tree, name: str) -> List[Tree]:
  """
  Find all children with given rule name.

  Args:
      tree: Parent tree to search
      name: Rule name to find

  Returns:
      List of all matching child trees
  """
  if not isinstance(tree, Tree):
    return []

  return [child for child in tree.children if isinstance(child, Tree) and child.data == name]


def text_to_tokens(text: str):
  """
  Convert text string to token sequence.

  Delegates to common TokenFactory for consistent token creation.

  Args:
      text: Text to tokenize

  Returns:
      List of typed tokens
  """
  return TokenFactory.from_text(text)
