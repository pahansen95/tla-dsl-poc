#!/usr/bin/env python3
"""
CST Navigation Utilities

Tools for traversing and querying Concrete Syntax Trees.
"""

from typing import Optional, List
from lark import Tree, Token


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


def text_to_tokens(text: str) -> List[Token]:
  """
  Convert text string to token sequence.

  Classifies tokens by type (WORD, NUMBER, SYMBOL) and
  inserts whitespace tokens between words.

  Args:
      text: Text to tokenize

  Returns:
      List of typed tokens
  """
  tokens = []
  words = text.split()

  for i, word in enumerate(words):
    # Classify token type
    if word.isdigit():
      token_type = "NUMBER"
    elif word.isalpha() or "_" in word:
      token_type = "WORD"
    else:
      token_type = "SYMBOL"

    tokens.append(Token(token_type, word))

    # Add space between words
    if i < len(words) - 1:
      tokens.append(Token("WS", " "))

  return tokens


def get_position(node: Tree | Token) -> dict:
  """
  Extract position metadata from CST node.

  Args:
      node: Tree or Token to extract position from

  Returns:
      Dictionary with line, column, end_line, end_column
  """
  meta = {}
  source = getattr(node, "meta", node) if hasattr(node, "meta") else node

  for attr in ["line", "column", "end_line", "end_column"]:
    if hasattr(source, attr) and (val := getattr(source, attr)) is not None:
      meta[attr] = val

  return meta
