#!/usr/bin/env python3
"""
DSL Parser Module

This module provides the core parsing functionality for the Natural Language
Specification DSL. It creates Lark parsers from grammar definitions and parses
DSL documents into Concrete Syntax Trees (CST).

Responsibilities:
- Create configured Lark parser instances from grammar strings
- Parse DSL documents into CST structures
- Provide a clean interface for parsing operations

The module focuses solely on the transformation from text to CST, maintaining
separation of concerns from serialization, unparsing, and display logic.
"""

from lark import Lark, Tree, exceptions
from typing import Optional


def create_parser(grammar: str, start: str = "specification", debug: bool = False) -> Lark:
  """
  Create a Lark parser instance configured for the DSL grammar.

  Args:
      grammar: The grammar definition in Lark EBNF format
      start: The starting rule name (default: "specification")
      debug: Enable debug output during parsing

  Returns:
      Configured Lark parser instance

  Raises:
      exceptions.GrammarError: If the grammar is invalid
  """
  return Lark(
    grammar,
    start=start,
    parser="earley",  # Handles all context-free grammars
    ambiguity="resolve",  # Auto-resolve ambiguities
    keep_all_tokens=True,  # Preserve all tokens for unparsing
    debug=debug,
  )


def parse_document(parser: Lark, document: str) -> Tree:
  """
  Parse a DSL document into a Concrete Syntax Tree.

  Args:
      parser: Configured Lark parser instance
      document: DSL document text to parse

  Returns:
      Parsed CST as a Tree object

  Raises:
      exceptions.UnexpectedCharacters: Invalid character in document
      exceptions.UnexpectedToken: Invalid token sequence
      exceptions.ParseError: General parsing failure
  """
  return parser.parse(document)


def parse_with_grammar(grammar: str, document: str, start: str = "specification") -> Tree:
  """
  Convenience function to parse a document with a grammar in one step.

  Args:
      grammar: Grammar definition string
      document: Document to parse
      start: Starting rule name

  Returns:
      Parsed CST
  """
  parser = create_parser(grammar, start)
  return parse_document(parser, document)


def validate_grammar(grammar: str) -> Optional[str]:
  """
  Validate a grammar definition without parsing a document.

  Args:
      grammar: Grammar definition to validate

  Returns:
      None if valid, error message if invalid
  """
  try:
    create_parser(grammar)
    return None
  except exceptions.GrammarError as e:
    return str(e)
  except Exception as e:
    return f"Unexpected error: {e}"
