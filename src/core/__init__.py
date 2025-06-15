#!/usr/bin/env python3
"""
Core DSL Processing Package - Refactored

This refactored version simplifies the package interface by:
- Removing redundant function imports (parse_with_grammar, validate_grammar)
- Streamlining the public API to essential functions only
- Maintaining clean separation between modules
- Reducing boilerplate with direct imports

The package provides fundamental components for parsing, transforming,
and unparsing Natural Language Specification DSL documents.
"""

# Parser functions - core parsing operations
from .parser import create_parser, parse_document

# Unparser functions - text reconstruction
from .unparser import unparse_tree, extract_tokens

# Serialization functions - CST pipeline support
from .syntax import serialize_cst, deserialize_cst, to_dict, from_dict

# Module version
__version__ = "0.1.0"

# Simplified public API - only essential functions
__all__ = [
  # Parser
  "create_parser",
  "parse_document",
  # Unparser
  "unparse_tree",
  "extract_tokens",
  # Serialization
  "serialize_cst",
  "deserialize_cst",
  "to_dict",
  "from_dict",
]
