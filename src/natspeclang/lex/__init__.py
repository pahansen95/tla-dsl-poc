"""Natural Specification Language lexical analysis package.

Provides integrated lexing, parsing, AST construction, and formatting
for NSL specifications. The package exposes a simple high-level API
while allowing access to individual components for advanced usage.
"""

# Import all public API components from their modules
from .ast import Specification, Concept, StateDeclaration, Operation, Property
from .tokenize import DSLLexer
from .parse import DSLParser
from .transform import ASTBuilder
from .format import ASTFormatter
from .serde import (
  serialize_ast,
  deserialize_ast,
  serialize_cst,
  deserialize_cst,
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
  # Serialization
  "serialize_ast",
  "deserialize_ast",
  "serialize_cst",
  "deserialize_cst",
]
