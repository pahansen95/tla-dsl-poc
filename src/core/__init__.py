#!/usr/bin/env python3
"""
Core DSL Processing Package

This package provides the fundamental components for parsing, transforming,
and unparsing Natural Language Specification DSL documents. It maintains a
clean separation of concerns with each module handling a specific aspect of
the document processing pipeline.

Modules:
- parser: Convert DSL text to Concrete Syntax Trees
- unparser: Convert CST back to DSL text
- syntax: Serialize/deserialize CST for pipeline processing

The package design enables flexible composition of these components for
various workflows including validation, transformation, and analysis.
"""

# Import key functions for convenient access
from .parser import create_parser, parse_document, parse_with_grammar, validate_grammar

from .unparser import unparse_tree, unparse_subtree, extract_tokens, unparse_without_whitespace

from .syntax import serialize_cst, deserialize_cst, to_dict, from_dict, roundtrip_test

# Module version
__version__ = "0.1.0"

# Public API
__all__ = [
  # Parser functions
  "create_parser",
  "parse_document",
  "parse_with_grammar",
  "validate_grammar",
  # Unparser functions
  "unparse_tree",
  "unparse_subtree",
  "extract_tokens",
  "unparse_without_whitespace",
  # Serialization functions
  "serialize_cst",
  "deserialize_cst",
  "to_dict",
  "from_dict",
  "roundtrip_test",
]
