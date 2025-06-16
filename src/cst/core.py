#!/usr/bin/env python3
"""
Core CST Operations

Fundamental parsing and unparsing operations for Concrete Syntax Trees.
"""

from lark import Lark, Tree, Token
from typing import Union
from common import extract_raw_text


def parse_document(grammar: str, document: str, start: str = "specification", debug: bool = False) -> Tree:
  """
  Parse DSL document into Concrete Syntax Tree.

  Args:
      grammar: Grammar definition in Lark format
      document: DSL document text
      start: Starting rule name
      debug: Enable parser debugging

  Returns:
      Parsed CST as Tree object

  Raises:
      exceptions.UnexpectedCharacters: Invalid character
      exceptions.UnexpectedToken: Invalid token sequence
      exceptions.ParseError: General parsing failure
  """
  parser = Lark(
    grammar,
    start=start,
    parser="earley",
    ambiguity="resolve",
    keep_all_tokens=True,
    debug=debug,
  )

  return parser.parse(document)


def unparse_tree(node: Union[Tree, Token]) -> str:
  """
  Reconstruct text from Concrete Syntax Tree.

  Uses common text extraction to concatenate all token values,
  preserving original document formatting.

  Args:
      node: Lark Tree or Token from the CST

  Returns:
      Text representation of the node and all children
  """
  return extract_raw_text(node)
