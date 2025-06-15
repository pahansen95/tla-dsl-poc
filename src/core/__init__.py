#!/usr/bin/env python3
"""
Core DSL Processing Package

This package provides fundamental components for parsing, transforming,
and unparsing Natural Language Specification DSL documents.

Now includes AST functionality for semantic analysis and transformation.
"""

# Parser functions - core parsing operations
from .parser import create_parser, parse_document

# Unparser functions - text reconstruction
from .unparser import unparse_tree, extract_tokens

# CST Serialization functions - pipeline support
from .syntax import serialize_cst, deserialize_cst, to_dict, from_dict

# AST functions - semantic representation
from .ast import (
  # Core transformation functions
  build_ast,
  format_ast,
  serialize_ast,
  deserialize_ast,
  ast_to_dict,
  ast_from_dict,
  # Node types (for type hints and instanceof checks)
  ASTNode,
  Specification,
  Concept,
  StateDeclaration,
  Operation,
  Constraint,
  Guarantee,
  # Visitor pattern
  ASTVisitor,
)

# Module version
__version__ = "0.2.0"

# Public API
__all__ = [
  # Parser
  "create_parser",
  "parse_document",
  # Unparser
  "unparse_tree",
  "extract_tokens",
  # CST Serialization
  "serialize_cst",
  "deserialize_cst",
  "to_dict",
  "from_dict",
  # AST Operations
  "build_ast",
  "format_ast",
  "serialize_ast",
  "deserialize_ast",
  "ast_to_dict",
  "ast_from_dict",
  # AST Types
  "ASTNode",
  "Specification",
  "Concept",
  "StateDeclaration",
  "Operation",
  "Constraint",
  "Guarantee",
  "ASTVisitor",
]
