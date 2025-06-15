#!/usr/bin/env python3
"""
AST Package Interface

This module provides a unified interface to the AST functionality,
exposing the key components needed for CST/AST transformations.
"""

# Import all node types for direct access
from .nodes import (
  ASTNode,
  Specification,
  Concept,
  StateDeclaration,
  Operation,
  Constraint,
  Guarantee,
  ASTVisitor,
  # Utility functions
  find_nodes_by_type,
  get_state_names,
  get_operation_triggers,
)

# Import transformation functions
from .builder import build_ast, CSTToASTBuilder, TextExtractor
from .formatter import format_ast, CanonicalFormatter
from .serializer import (
  serialize_ast,
  deserialize_ast,
  to_dict as ast_to_dict,
  from_dict as ast_from_dict,
  roundtrip_test as ast_roundtrip_test,
)

# Version
__version__ = "0.1.0"

# Public API
__all__ = [
  # Node classes
  "ASTNode",
  "Specification",
  "Concept",
  "StateDeclaration",
  "Operation",
  "Constraint",
  "Guarantee",
  "ASTVisitor",
  # Builder
  "build_ast",
  "CSTToASTBuilder",
  "TextExtractor",
  # Formatter
  "format_ast",
  "CanonicalFormatter",
  # Serializer
  "serialize_ast",
  "deserialize_ast",
  "ast_to_dict",
  "ast_from_dict",
  "ast_roundtrip_test",
  # Utilities
  "find_nodes_by_type",
  "get_state_names",
  "get_operation_triggers",
]
