"""Natural Specification Language lexical analysis package.

Provides integrated lexing, parsing, AST construction, and formatting
for NSL specifications. The package exposes a simple high-level API
while allowing access to individual components for advanced usage.
"""

# Import all public API components from their modules
from .ast import Specification, Concept, StateDeclaration, Operation, Property
from .tokenize import DSLLexer
from .parse import DSLParser, parse
from .transform import ASTBuilder
from .format import ASTFormatter, format_ast
from .serde import (
  serialize_ast,
  deserialize_ast,
  serialize_cst,
  deserialize_cst,
  parse_to_json,
  format_from_json,
)


__all__ = [
  # AST nodes
  "Specification",
  "Concept",
  "StateDeclaration",
  "Operation",
  "Property",
  # Core classes
  "DSLLexer",
  "DSLParser",
  "ASTBuilder",
  "ASTFormatter",
  # High-level functions
  "parse",
  "format_ast",
  "parse_to_json",
  "format_from_json",
  # Serialization
  "serialize_ast",
  "deserialize_ast",
  "serialize_cst",
  "deserialize_cst",
]
