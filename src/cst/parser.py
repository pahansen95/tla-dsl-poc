#!/usr/bin/env python3
"""
CST Parser Module

Handles parsing of DSL documents into Concrete Syntax Trees.
"""

from lark import Lark, Tree


def parse_document(grammar: str, document: str, start: str = "specification", debug: bool = False) -> Tree:
  """
  Parse a DSL document into a Concrete Syntax Tree.

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
    keep_all_tokens=True,  # Preserve all tokens for unparsing
    debug=debug,
  )

  return parser.parse(document)
